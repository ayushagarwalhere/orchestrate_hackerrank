"""Independent counterexamples for the investigation's evidence boundaries."""
import csv
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.inspect_participant_evidence import contains_identifier, inspect_corpus, inspect_sql, leaves
from test_workflow import req, act
from workflow import assign_workflows
from evidence.index import EvidenceIndex
from evidence.model import Coverage, State
from identity import parse_ts


@pytest.mark.parametrize("value,expected", [
    ("account_82", True), ("[account_82]", True),
    ("account_820", False), ("other_account_82", False),
    ("account_82_old", False), ("account_082", False)])
def test_exact_namespace_and_numeric_boundaries(value, expected):
    assert contains_identifier(value, "account_82") is expected


def test_json_pointer_retains_exact_location_and_decoded_value():
    document = json.loads('{"a/b~c":[{"reference":"account_\\u0038\\u0032"}]}')
    assert list(leaves(document)) == [("/a~1b~0c/0/reference", "account_82")]


def test_sql_inspection_preserves_explicit_relationships(tmp_path):
    path = tmp_path / "snapshot.sql"
    path.write_text('CREATE TABLE subject(id TEXT PRIMARY KEY);'
                    'CREATE TABLE record(owner TEXT REFERENCES subject(id), record_json TEXT);'
                    "INSERT INTO subject VALUES ('person_z');"
                    "INSERT INTO record VALUES ('person_z', '{\"resource\":\"record_82\"}');", encoding="utf-8")
    tables = {t["table"]: t for t in inspect_sql(path)}
    assert tables["record"]["foreign_keys"][0]["table"] == "subject"
    assert tables["record"]["rows"][0]["owner"] == "person_z"
    assert json.loads(tables["record"]["rows"][0]["record_json"])["resource"] == "record_82"


def test_sql_inspection_rejects_external_database_effects(tmp_path):
    path = tmp_path / "unsafe.sql"
    external = tmp_path / "external.db"
    path.write_text("ATTACH DATABASE '" + str(external).replace("'", "''") + "' AS extra;", encoding="utf-8")
    with pytest.raises(sqlite3.DatabaseError):
        inspect_sql(path)
    assert not external.exists()


def test_corpus_does_not_read_answers_and_separates_missing_from_failure(tmp_path):
    data = tmp_path / "dataset"
    evidence = data / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "good.json").write_text('{"records":[{"id":"record_82"}]}', encoding="utf-8")
    (evidence / "broken.json").write_text('{bad', encoding="utf-8")
    with (data / "evidence_files.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_id", "file_path", "origin", "captured_at"])
        for ident, filename in [("source_a", "good.json"), ("source_b", "broken.json")]:
            writer.writerow([ident, "evidence/" + filename, "test", "2026-05-03T00:00:00Z"])
    for filename in ("sample_output.csv", "output.csv", "golden_fixture.json"):
        (data / filename).write_text("secret_answer_17", encoding="utf-8")
    report = inspect_corpus(data, ["record_82", "secret_answer_17", "record_99"])
    assert {h["target"] for h in report["exact_hits"]} == {"record_82"}
    decoded = [h for h in report["exact_hits"] if h["representation"] == "decoded_json"]
    assert decoded[0]["location"] == "/records/0/id"
    assert decoded[0]["source_id"] == "source_a"
    assert decoded[0]["captured_at"] == "2026-05-03T00:00:00+00:00"
    assert report["errors"] == [{"source_id": "source_b", "error_type": "JSONDecodeError"}]
    assert all("answer" not in f["path"] and "fixture" not in f["path"] for f in report["files"])


def test_failed_event_order_is_reported_as_heuristic_not_ownership():
    events = [act("event_a", -50, "account_red"), act("event_b", -40, "account_blue")]
    first = assign_workflows([req("case_7", "person_x"), req("case_8", "person_y")], events, {})
    renamed = assign_workflows([req("case_9", "person_x"), req("case_8", "person_y")], events, {})
    assert first["case_7"]["account"].method == "tie-break"
    assert renamed["case_9"]["account"].method == "tie-break"
    assert first["case_7"]["account"].resource_id != renamed["case_9"]["account"].resource_id


def test_subject_bearing_ownership_overrides_order_and_numeric_labels():
    events = [act("event_a", -50, "account_red"), act("event_b", -40, "account_blue")]
    result = assign_workflows([req("case_7", "person_x"), req("case_8", "person_y")], events,
                              {"account_blue": {"person_x"}, "account_red": {"person_y"}})
    assert result["case_7"]["account"].resource_id == "account_blue"
    assert result["case_7"]["account"].method == "own-identifier"


def test_blanket_absence_establishes_state_without_subject_ownership():
    time = parse_ts("2026-09-05T12:00:00Z")
    coverage = Coverage("source_empty", time, time, "account_service", kind="empty_snapshot",
                        source="/profiles", covered_scopes=("/profiles",))
    index = EvidenceIndex([], [coverage], [], [], [])
    for resource in ("account_880001", "account_880002"):
        observation = index.omission(resource, time)
        assert observation.state is State.ABSENT
        assert not observation.link_keys
    assert not index.by_key
    assert index.omission("audit_record_880001", time) is None


def test_failed_delete_claim_alone_is_neither_state_nor_ownership():
    event = act("event_a", -50, "account_red")
    index = EvidenceIndex([], [], [], [event], [])
    assert index.state_at("account_red", event.event_time) is None
    assert not index.matching({("user", "person_x")})
