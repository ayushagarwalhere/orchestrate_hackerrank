"""Independent intent and extraction-boundary regressions; no sample answers."""
import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark_agent import AuditAgent
from audit_tools import AuditTools
from evidence.common import EvidenceFile
from evidence.index import EvidenceIndex, build
from evidence.ledger import (EvidenceCoverageError, ExtractionStatus, extract_corpus)
from evidence.model import Presence, State
from evidence import documents, images, records, sql
from intent import (DELETION, NOT_APPLICABLE, UNSURE, FALLBACK_PROMPT, SCHEMA,
                    UnresolvedIntentError, classify, classify_with_fallback, valid_assessment)
from investigate import CaseInvestigation
from identity import parse_ts
from llm import CachedLLM, Usage, cache_key

AT = parse_ts("2026-06-03T12:00:00Z")


@pytest.mark.parametrize("text,kind", [
    ("Delete my personal data.", "deletion"),
    ("Please give me access to the information you hold about me.", "access"),
    ("Please correct my misspelled surname.", "correction"),
    ("Please remove my name and replace it with the correct spelling.", "correction"),
    ("Please export a copy of my data.", "export"),
    ("Please remove my email from your marketing list.", "marketing_opt_out"),
    ("Please remove me from marketing lists only.", "marketing_opt_out"),
    ("Restore my account.", "restoration"),
    ("How do I delete my account?", "question"),
    ("How to delete my account?", "question"),
    ("Can you explain how to delete my account?", "question"),
    ("Please show me how to delete my account.", "question"),
    ("Do you delete records after three years?", "question"),
    ("Can a deleted account be restored?", "question"),
])
def test_request_types_are_distinct(text, kind):
    result = classify(text)
    assert result.intent == kind
    assert result.label == (DELETION if kind == "deletion" else NOT_APPLICABLE)


@pytest.mark.parametrize("text", [
    "Delete my personal data. You may retain legally required records.",
    "Delete my account, but you can keep the security audit logs if required by law.",
    "Remove my personal information except legally required records.",
    "Erase my personal data. Do not delete legally required invoices.",
    "Please remove my personal details, but keeping an internal reference is fine if retained records need it.",
])
def test_retention_does_not_negate_deletion(text):
    result = classify(text)
    assert result.label == DELETION
    assert result.retention_allowed is True


@pytest.mark.parametrize("text", [
    "Please delete my account if the export succeeds.",
    "Please delete my account if the export succeeds and keep legally required records.",
    "Delete my account. Do not delete my account.",
    "Please delete my account but keep the account active.",
    "Maybe erase my account.",
    "I need my profile gone for good.",
])
def test_ambiguous_or_conditional_authorization_remains_uncertain(text):
    assert classify(text).label == UNSURE
    assert classify_with_fallback(text).label == UNSURE


@pytest.mark.parametrize("text", [
    'Please export the message "delete my account".',
    "I want an export of my deleted records.",
    "My account was deleted by mistake. Please restore it.",
    "I don't want you to delete my account.",
    "I do not authorize you to erase my personal data. Retain legally required records.",
    "There is no permission to delete my account.",
    "I withdraw my request to delete my account.",
])
def test_mentions_and_quotes_are_not_authorization(text):
    assert classify(text).label == NOT_APPLICABLE


def response(text, **changes):
    value = {"label": DELETION, "intent": "deletion", "retention_allowed": None,
             "negated": False, "conditional": False, "spans": [{"start": 0, "end": len(text)}]}
    return dict(value, **changes)


class FakeClient:
    provider, model = "fake", "test"
    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.calls, self.prompts = answer, error, 0, []
    def generate_json(self, prompt, images=()):
        self.calls += 1; self.prompts.append(prompt)
        if self.error: raise self.error
        return self.answer, Usage(12, 5)


def test_only_ambiguous_intent_uses_versioned_prompt_and_revalidated_cache(tmp_path):
    text = "I need my profile gone for good."
    client = FakeClient(response(text)); llm = CachedLLM(client, cache_dir=tmp_path)
    assert classify_with_fallback("Please erase my account.", llm).label == DELETION
    assert client.calls == 0
    assert classify_with_fallback(text, llm).label == DELETION
    assert client.calls == 1
    assert "UNTRUSTED DATA" in client.prompts[0] and json.dumps(text) in client.prompts[0]
    assert FALLBACK_PROMPT.name == "intent_fallback_v3.md"
    offline = CachedLLM(provider="fake", model="test", cache_dir=tmp_path)
    assert classify_with_fallback(text, offline).label == DELETION
    path = next(tmp_path.glob("*.json")); cached = json.loads(path.read_text())
    cached["response"]["spans"] = [{"start": 0, "end": 9999}]
    path.write_text(json.dumps(cached)); old_bytes = path.read_bytes()
    assert classify_with_fallback(text, llm).label == UNSURE
    assert client.calls == 1 and path.read_bytes() == old_bytes


@pytest.mark.parametrize("changes", [
    {"tool": "shell"}, {"conditional": True}, {"negated": True}, {"label": "COMPLETE"},
    {"spans": []}, {"spans": [{"start": True, "end": 2}]}, {"retention_allowed": "yes"},
])
def test_malformed_classifications_do_not_publish_confident_labels(tmp_path, changes):
    text = "I need my profile gone for good."
    client = FakeClient(response(text, **changes)); llm = CachedLLM(client, cache_dir=tmp_path)
    assert classify_with_fallback(text, llm).label == UNSURE
    assert not list(tmp_path.glob("*.json"))


def test_parser_provider_and_budget_failures_preserve_uncertainty(tmp_path, monkeypatch):
    text = "I need my profile gone for good."
    llm = CachedLLM(FakeClient(error=RuntimeError("secret/customer text")), cache_dir=tmp_path)
    result = classify_with_fallback(text, llm)
    assert (result.label, result.rule) == (UNSURE, "model_provider_failed")
    client = FakeClient(response(text)); limited = CachedLLM(client, cache_dir=tmp_path, max_live_calls=0)
    assert classify_with_fallback(text, limited).rule == "model_budget_exhausted"
    assert client.calls == 0
    monkeypatch.setattr("intent.normalize", Mock(side_effect=RuntimeError("secret")))
    assert classify_with_fallback(text, limited).rule == "parser_failure"
    with pytest.raises(UnresolvedIntentError):
        _ = CaseInvestigation("synthetic", UNSURE).status


def source(tmp_path, folder, suffix, body, identifier="source_a"):
    path = tmp_path / "dataset/evidence" / folder / (identifier + suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.encode() if isinstance(body, str) else body)
    return EvidenceFile(identifier, path, "synthetic", AT)


def corpus(files, tmp_path):
    return extract_corpus(files, (), tmp_path / "facts", render_dir=tmp_path / "renders")


def test_json_sql_text_and_logs_share_grounded_fields_and_locations(tmp_path):
    files = [
        source(tmp_path, "records", ".json", json.dumps({"collection": "customer_analytics_reports", "captured_at": AT.isoformat(),
            "records": [{"resource_id": "analytics_8402", "email": "a@example.test", "phone": None,
                         "email_hash": None, "user_id": None}]}), "json_source"),
        source(tmp_path, "databases", ".sql", "CREATE TABLE customer_profiles_primary(resource_id TEXT,email TEXT,phone TEXT); INSERT INTO customer_profiles_primary VALUES('account_7732','a@example.test','+44 020 1234');", "sql_source"),
        source(tmp_path, "records", ".txt", "CUSTOMER PLATFORM - SHIFT HANDOVER\n- 2026-06-03T12:00:00Z | account_service | account_2304 | USER_PROFILE | NOT_FOUND | a@example.test\n", "text_source"),
        source(tmp_path, "logs", ".log", "2026-06-03T12:00:00Z service=account_service trace_id=t event=profile_lookup_completed resource_id=account_3782 rows=0 http_status=404\n", "log_source"),
    ]
    obs, covers, missing, ledger = corpus(files, tmp_path)
    assert len(obs) == 4 and not missing and not covers
    assert len(ledger.files_processed) == 4
    for o in obs:
        assert o.source_id and o.system_id and o.resource_id and o.category and o.state
        assert o.observed_at == o.capture_time == AT
        assert o.source_location
    phone = next(f for o in obs if o.source_id == "sql_source" for f in o.identifying_fields if f.path == "/phone")
    assert phone.value_json == '"+44 020 1234"'
    fields = {f.path: f.presence for f in obs[0].identifying_fields}
    assert fields["/phone"] is Presence.NULL and fields["/name"] is Presence.MISSING


def test_empty_parser_result_is_not_absence_or_system_coverage(tmp_path):
    ef = source(tmp_path, "records", ".json", json.dumps({"collection": "customer_export_jobs", "captured_at": AT.isoformat(), "records": []}))
    obs, scopes, missing, ledger = corpus([ef], tmp_path)
    assert not obs and not scopes
    assert ledger.files[0].status is ExtractionStatus.EMPTY
    index = EvidenceIndex(obs, scopes, [], [], missing, ledger)
    assert index.state_at("export_9921", AT) is None
    assert not ledger.system_coverage


def test_file_failures_missing_extraction_and_unresolved_refs_are_separate(tmp_path):
    broken = source(tmp_path, "records", ".json", "not JSON", "broken")
    missing = source(tmp_path, "records", ".json", "{}", "missing"); missing.path.unlink()
    image = source(tmp_path, "images", ".png", b"synthetic", "image")
    odd = source(tmp_path, "records", ".csv", "opaque", "unsupported")
    obs, scopes, absent, ledger = corpus([broken, missing, image, odd], tmp_path)
    assert not obs and not scopes
    assert len(ledger.files) == 4 and len(ledger.extraction_failures) == 1 and len(ledger.missing_extraction) == 3
    assert absent == ["image"]
    with pytest.raises(EvidenceCoverageError): ledger.assert_ready()
    assert "synthetic" not in json.dumps(ledger.summary())


def test_unrecognized_records_do_not_disappear_as_successful_empty_reads(tmp_path):
    ef = source(tmp_path, "records", ".json", json.dumps({"collection": "unrecognized", "captured_at": AT.isoformat(),
                                                        "records": [{"resource_id": "account_7612"}]}))
    obs, scopes, missing, ledger = corpus([ef], tmp_path)
    assert not obs and not scopes
    assert ledger.unresolved_references[0].reason == "unrecognized_record"
    with pytest.raises(EvidenceCoverageError): ledger.assert_ready()


def test_missing_permission_or_identifier_fields_remain_unknown(tmp_path):
    from evidence.interpret import observe
    ctx = dict(evidence_id="s", file_captured_at=AT, observed_at=AT, location="/records/0")
    assert observe("connectors", {"resource_id": "data_flow_2001"}, ctx)[0].state is State.UNKNOWN
    assert observe("restore_entries", {"resource_id": "backup_2001"}, ctx)[0].state is State.UNKNOWN
    assert observe("restore_entries", {"resource_id": "backup_2001", "restore_allowed": "maybe"}, ctx)[0].state is State.UNKNOWN
    assert observe("profiles", {"resource_id": "analytics_2001"}, ctx)[0].state is State.UNKNOWN
    from investigate import resource_state
    from evidence.ledger import EvidenceResolutionError
    fact = observe("profiles", {"resource_id": "analytics_2001"}, ctx)[0]
    index = EvidenceIndex([fact], [], [], [], [])
    with pytest.raises(EvidenceResolutionError):
        resource_state(index, fact.resource_id, {"audit_at": AT.isoformat(), "requested_at": AT.isoformat()}, "synthetic")


def test_screenshot_unresolved_labels_are_not_invented_resources(tmp_path):
    ef = source(tmp_path, "images", ".png", b"synthetic", "image")
    facts = tmp_path / "facts"; facts.mkdir()
    (facts / "image.json").write_text(json.dumps({"file_id": "image", "records": [
        {"resource_id": "", "labels": ["external_file.pdf"], "category": "SUPPORT_ATTACHMENT", "state": "PRESENT"}]}))
    obs, scopes, missing, ledger = corpus([ef], tmp_path)
    assert not obs and not missing
    assert ledger.unresolved_references[0].reason == "unresolved_visual_reference"
    assert ledger.files[0].status is ExtractionStatus.EMPTY


def test_blank_screenshot_cache_requires_visual_review(tmp_path):
    ef = source(tmp_path, "images", ".png", b"synthetic", "image")
    facts = tmp_path / "facts"; facts.mkdir()
    (facts / "image.json").write_text(json.dumps({"file_id": "image", "records": []}))
    obs, _, _, ledger = corpus([ef], tmp_path)
    assert not obs and ledger.files[0].status is ExtractionStatus.REVIEW
    with pytest.raises(EvidenceCoverageError): ledger.assert_ready()


def test_blank_pdf_is_rendered_and_requires_inspection(tmp_path):
    from reportlab.pdfgen import canvas
    ef = source(tmp_path, "documents", ".pdf", b"", "pdf_source")
    pdf = canvas.Canvas(str(ef.path)); pdf.showPage(); pdf.save()
    obs, _, _, ledger = corpus([ef], tmp_path)
    assert not obs and (tmp_path / "renders/pdf_source-page-1.png").exists()
    assert ledger.files[0].status is ExtractionStatus.REVIEW
    issues = []
    def reader(source_file, page, rendered):
        assert source_file.file_id == "pdf_source" and page == 1 and rendered.is_file()
        return documents.VisualText("account_7781 a@example.test", True)
    obs = documents.load([ef], issues=issues, visual_reader=reader, render_dir=tmp_path / "renders")
    assert obs[0].source_location == "page:1" and obs[0].file_captured_at == AT


def test_index_built_once_and_reused_by_actual_coordinator(tmp_path, monkeypatch):
    from test_agent_workflow import FixtureTools
    index = SimpleNamespace(observations=[], coverages=[], activities=[], ledger=None)
    tools = FixtureTools(); seen = []
    def make_index(data): seen.append(index); return index
    def investigate(data, inputs, supplied, llm):
        assert supplied is index
        return {"test_1": SimpleNamespace(account=None, resources=[])}
    tools.index_evidence = make_index; tools.investigate = investigate
    AuditAgent(tools, backup_dir=tmp_path / "backups").run(tmp_path / "dataset", tmp_path / "out.csv")
    assert seen == [index]


def test_corpus_failure_blocks_publication_and_logs_only_aggregate_counts(tmp_path):
    from test_agent_workflow import FixtureTools
    ef = source(tmp_path, "records", ".json", "customer secret malformed", "broken")
    _, _, _, ledger = corpus([ef], tmp_path)
    class Tools(FixtureTools):
        def index_evidence(self, data): ledger.assert_ready()
    out, trace, ledger_path = tmp_path / "out.csv", tmp_path / "trace.json", tmp_path / "ledger.json"
    out.write_bytes(b"old validated output")
    ledger_path.write_text('{"old":"successful extraction"}')
    with pytest.raises(EvidenceCoverageError): AuditAgent(Tools()).run(tmp_path / "dataset", out, trace, ledger_path)
    assert out.read_bytes() == b"old validated output"
    data = trace.read_text(); assert "customer secret" not in data and "broken" not in data
    assert json.loads(data)["counts"]["extraction_failures"] == 1
    assert json.loads(ledger_path.read_text())["files"][0]["status"] == "FAILED"


def test_nonstandard_directories_do_not_make_files_disappear(tmp_path):
    ef = source(tmp_path, "unusual_folder", ".TXT", "CUSTOMER PLATFORM - SHIFT HANDOVER\n- 2026-06-03T12:00:00Z | account_service | account_8831 | USER_PROFILE | NOT_FOUND | a@example.test\n")
    obs, _, _, ledger = corpus([ef], tmp_path)
    assert obs[0].resource_id == "account_8831" and len(ledger.files_processed) == 1


def test_manifest_rejects_unsafe_source_ids(tmp_path):
    from evidence.common import load_manifest
    data = tmp_path / "data"; data.mkdir()
    (data / "evidence_files.csv").write_text("file_id,file_path,origin,captured_at\n../escape,evidence/file.pdf,test,2026-06-03T12:00:00Z\n")
    with pytest.raises(ValueError, match="safe identifier"): load_manifest(data)


def test_pdf_identifiers_preserve_visible_phone_and_unknown_names():
    from evidence.model import text_identifying_fields
    fields = text_identifying_fields("Customer: Example Name\nPhone: +44 020 1234\na@example.test")
    assert any(f.path.startswith("/phone/") and "+44 020 1234" in f.value_json for f in fields)
    assert next(f for f in fields if f.path == "/name").presence is Presence.UNKNOWN


def test_ledger_round_trip_contains_observations_and_source_clocks(tmp_path):
    ef = source(tmp_path, "records", ".json", json.dumps({"collection": "customer_export_jobs", "captured_at": AT.isoformat(),
                                                        "records": [{"resource_id": "export_8831", "owner_email": "a@example.test"}]}))
    obs, _, _, ledger = corpus([ef], tmp_path)
    out = tmp_path / "ledger.json"; ledger.write(out); value = json.loads(out.read_text())
    assert value["observations"][0]["resource_id"] == "export_8831"
    assert value["observations"][0]["file_captured_at"] == AT.isoformat()
    assert value["files"][0]["content_sha256"] == hashlib.sha256(ef.path.read_bytes()).hexdigest()


def test_malformed_screenshot_identifiers_are_extraction_failures(tmp_path):
    ef = source(tmp_path, "images", ".png", b"synthetic", "image")
    facts = tmp_path / "facts"; facts.mkdir()
    (facts / "image.json").write_text(json.dumps({"file_id": "image", "records": [
        {"resource_id": "account_1442", "category": "USER_PROFILE", "state": "PRESENT", "emails": "wrong type"}]}))
    _, _, _, ledger = corpus([ef], tmp_path)
    assert len(ledger.extraction_failures) == 1


def test_ledger_path_cannot_overwrite_source_or_output(tmp_path):
    from test_agent_workflow import FixtureTools
    agent = AuditAgent(FixtureTools())
    with pytest.raises(ValueError, match="Ledger"):
        agent.run(tmp_path / "dataset", tmp_path / "out.csv", ledger_path=tmp_path / "dataset/ledger.json")
    with pytest.raises(ValueError, match="Ledger"):
        agent.run(tmp_path / "dataset", tmp_path / "out.csv", ledger_path=tmp_path / "out.csv")


def test_catalog_identity_label_does_not_hide_unresolved_document_rows(tmp_path, monkeypatch):
    ef = source(tmp_path, "documents", ".pdf", b"synthetic", "register")
    monkeypatch.setattr(documents, "page_texts", lambda *args: iter([(1, "ORD-44531 | user_09 | retained order")]))
    link = SimpleNamespace(label="user_09", resource_id="tombstone_8871")
    issues = []; obs = documents.load([ef], (link,), issues=issues)
    assert not obs
    row = next(i for i in issues if i.reason == "external_document_reference")
    assert row.reference == "ORD-44531" and row.identifying_keys == {("user", "user_09")}
    assert row.identifying_fields and row.location == "page:1/line:1"
    assert any(i.reason == "unclassified_document_reference" for i in issues)
