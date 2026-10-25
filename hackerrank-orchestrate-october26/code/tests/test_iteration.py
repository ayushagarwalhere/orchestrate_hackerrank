"""Measured-failure regressions with synthetic subjects; references stay in evaluation."""
from dataclasses import replace
import csv
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_workflow as workflow
from test_workflow import AT, BEFORE, Spy, fixture
from audit_agent import AuditFailure, default_tools
from audit_agent.contracts import (Artifact, CompilationInput, ExtractionInput, IndexInput, InvestigationInput,
                                   LoadInput, ValidationInput, timestamp)
from audit_agent.evidence import EvidenceGap, FieldPresence, Identifier, IdentifierKind, Permission, State
from audit_agent.investigation import request_authorizes
from audit_agent.readbacks import json_evidence, log_evidence, media_evidence, sql_evidence
from evaluation.sample_eval import compare, compare_runs, differences, predict, read_frozen


def artifact(suffix, content):
    content = content.encode() if isinstance(content, str) else content
    return Artifact("source_independent", suffix, timestamp(AT), content, hashlib.sha256(content).hexdigest())


class IntentRegressions(unittest.TestCase):
    def test_courtesy_condition_does_not_change_explicit_deletion(self):
        self.assertTrue(request_authorizes("Please erase my account. Contact me if verification is needed."))
        self.assertTrue(request_authorizes("Close the account completely. Backups may stay if policy requires."))

    def test_conditions_and_conflicts_on_deletion_remain_unknown(self):
        for text in ["Delete my account if my order arrives.", "If I move, please delete my account.",
                     "Please delete my account only after I approve.",
                     "Please erase my account. Do not delete my account."]:
            with self.subTest(text=text), self.assertRaises(AuditFailure):
                request_authorizes(text)

    def test_explicit_retrospective_audit(self):
        for text in ["I closed my account. Please check for remaining copies.",
                     "Could you verify that my account was deleted?",
                     "The account itself is gone. Please remove remaining traces."]:
            with self.subTest(text=text): self.assertTrue(request_authorizes(text))

    def test_full_account_multilingual_and_unknown_scope(self):
        for text in ["Je demande la suppression de mon compte.", "Quiero eliminar mi cuenta.",
                     "アカウントの削除をお願いします。"]:
            with self.subTest(text=text): self.assertTrue(request_authorizes(text))
        for text in ["Please erase my marketing profile permanently.", "I need my profile gone for good.",
                     "No quiero eliminar mi cuenta.", "Je ne demande pas la suppression de mon compte."]:
            with self.subTest(text=text), self.assertRaises(AuditFailure): request_authorizes(text)


class ReadbackRegressions(unittest.TestCase):
    def test_nested_snapshot_binds_owner_without_suffix_join(self):
        source = artifact(".json", json.dumps({"exported_at": AT, "snapshots": [{"collection": "customer_profiles",
            "captured_at": BEFORE, "records": [{"resource_id": "opaque_profile", "email": "a@example.test"}]}]}))
        bundle = json_evidence(source)
        self.assertEqual(bundle.observations[0].resource_id, "opaque_profile")
        self.assertEqual(bundle.ownership_links[0].identifier.raw, "a@example.test")
        self.assertEqual(bundle.observations[0].available_at, timestamp(AT))

    def test_sql_physical_copies_and_table_scope(self):
        bundle = sql_evidence(artifact(".sql", """
CREATE TABLE customer_profiles_primary (resource_id TEXT, email TEXT);
CREATE TABLE customer_profiles_failover_replica (resource_id TEXT, email TEXT);
INSERT INTO customer_profiles_failover_replica VALUES ('opaque_profile','a@example.test');
"""))
        self.assertEqual(len(bundle.observations), 1)  # Empty primary is not global absence.
        fact = bundle.observations[0]
        self.assertEqual(fact.copy_id, "customer_profiles_failover_replica")
        self.assertEqual(fact.scope.covered_tables, ("customer_profiles_failover_replica",))

    def test_sql_cannot_attach_disk_or_invoke_unapproved_functions(self):
        for sql in ["ATTACH DATABASE 'file.db' AS external;", "SELECT load_extension('anything');"]:
            with self.subTest(sql=sql), self.assertRaises(Exception): sql_evidence(artifact(".sql", sql))

    def test_log_trace_keeps_lookup_ownership_separate_from_absence(self):
        bundle = log_evidence(artifact(".log",
            f'{BEFORE} service=account_service trace_id=t event=profile_lookup_started lookup_key=a@example.test\n'
            f'{AT} service=account_service trace_id=t event=profile_lookup_completed resource_id=opaque_profile http_status=404\n'))
        self.assertEqual(bundle.observations[0].state, State.ABSENT)
        self.assertEqual(bundle.ownership_links[0].identifier.raw, "a@example.test")
        self.assertEqual(bundle.observations[0].permissions[0].value, Permission.UNKNOWN)

    def test_media_row_does_not_cross_join_other_customers(self):
        lines = [dict(text="marketing_908 a@example.test"), dict(text="marketing_173 b@example.test")]
        with patch("audit_agent.readbacks.image_text", return_value={"text": "\n".join(r['text'] for r in lines), "lines": lines}):
            bundle = media_evidence(artifact(".png", b"fake local OCR"), ())
        self.assertEqual([(l.resource_id, l.identifier.raw) for l in bundle.ownership_links],
                         [("marketing_908", "a@example.test"), ("marketing_173", "b@example.test")])

    def test_unrepresented_media_is_a_coverage_gap_without_invented_id(self):
        data = {"text": "Customer a@example.test", "lines": [{"text": "Customer a@example.test"}]}
        with patch("audit_agent.readbacks.image_text", return_value=data):
            bundle = media_evidence(artifact(".png", b"fake local OCR"), ())
        self.assertFalse(bundle.observations)
        self.assertEqual(bundle.gaps[0].source_id, "source_independent")
        self.assertEqual(bundle.gaps[0].identifiers[0].raw, "a@example.test")

    def test_missing_fields_are_unknown_not_anonymized_or_policy_witnesses(self):
        bundle = log_evidence(artifact(".log", f'{AT} service=analytics_platform event=analytics_profile_read resource_id=opaque\n'))
        self.assertEqual(bundle.observations[0].state, State.UNKNOWN)
        fields = {f.name: f.presence for f in bundle.observations[0].fields}
        self.assertEqual(fields["email"], FieldPresence.MISSING)
        bundle = log_evidence(artifact(".log", f'{AT} service=support_platform event=support_ticket_read_completed resource_id=opaque requester_email=a@example.test\n'))
        self.assertNotIn("shared_context", bundle.observations[0].conditions)

    def test_lookup_selector_does_not_establish_exposed_analytics_pii(self):
        bundle = log_evidence(artifact(".log",
            f'{BEFORE} service=analytics_platform trace_id=t event=analytics_profile_read_started lookup_key=a@example.test\n'
            f'{AT} service=analytics_platform trace_id=t event=analytics_profile_read_completed resource_id=opaque email=null phone=null email_hash=null customer_reference=null\n'))
        self.assertEqual(bundle.observations[0].state, State.ANONYMIZED)
        self.assertEqual(bundle.ownership_links[0].identifier.raw, "a@example.test")


class EvaluationRegressions(unittest.TestCase):
    setUp = workflow.WorkflowTests.setUp

    def sample_fixture(self):
        requests = [[f"sample_{n}", "beta@example.test", BEFORE, "NOT_STARTED", BEFORE, AT,
                     "Please erase my account."] for n in range(32)]
        config = fixture(self.root, requests=requests)
        (config.dataset / "deletion_requests.csv").rename(config.dataset / "sample_deletion_requests.csv")
        return config

    def test_predict_never_opens_reference_and_indexes_once(self):
        config = self.sample_fixture()
        tools = default_tools(); index = Spy(tools.index)
        tools = replace(tools, index=index)
        original = Path.open
        def guard(path, *args, **kwargs):
            if path.name == "sample_output.csv": raise AssertionError("Reference leakage")
            return original(path, *args, **kwargs)
        run = self.root / "frozen"
        with patch.object(Path, "open", guard): manifest = predict(config.dataset, run, tools=tools)
        self.assertEqual(manifest["predicted_cases"], 32)
        self.assertEqual(len(index.calls), 1)
        with self.assertRaises(ValueError): predict(config.dataset, run)
        (run / "predictions.csv").write_bytes(b"tampered")
        with self.assertRaises(ValueError): read_frozen(run)

    def test_comparator_reports_each_field_numbering_and_order(self):
        def step(resource, n):
            return dict(phase="VERIFICATION", system_id="svc", resource_id=resource,
                        operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id="src", step_no=n)
        a, b = step("opaque_a", 1), step("opaque_b", 2)
        actual = [dict(b, step_no=1, evidence_id="other"), dict(a, step_no=2, state="PRESENT")]
        delta = differences(actual, [a, b])
        self.assertTrue(delta["order_error"])
        fields = set().union(*(e["fields"] for e in delta["field_errors"]))
        self.assertEqual(fields, {"step_no", "evidence_id", "state"})
        for field, value in [("resource_id", "wrong"), ("operation", "VERIFY_RECORD_PRESENT"), ("system_id", "wrong")]:
            delta = differences([dict(a, **{field: value})], [a])
            # A changed system can be reported as explicit missing/extra rather
            # than guessing correspondence across unrelated resources.
            self.assertTrue(delta["field_errors"] or (delta["missing_steps"] and delta["extra_steps"]))

    def test_missing_prediction_counts_in_all_case_denominators(self):
        config = self.sample_fixture(); run = self.root / "frozen"
        tools = default_tools()
        def fail(value): raise AuditFailure(workflow.FailureType.UNSUPPORTED)
        predict(config.dataset, run, tools=replace(tools, extract=Spy(tools.extract, fail)))
        with (config.dataset / "sample_output.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream); writer.writerow(["case_id", "deletion_status", "steps_json"])
            writer.writerows([[f"sample_{n}", "COMPLETE", "[]"] for n in range(32)])
        metrics = compare(config.dataset, run, self.root / "report.md")
        self.assertEqual((metrics["cases"], metrics["status_correct"], metrics["full_case_exact"]), (32, 0, 0))
        self.assertEqual(metrics["sequence_exact"], 0)

    def test_architecture_bytes_and_correctness_explanations_are_enforced(self):
        config = self.sample_fixture()
        before, after = self.root / "before", self.root / "after"
        predict(config.dataset, before); predict(config.dataset, after)
        self.assertTrue(compare_runs(before, after, architectural=True)["identical_bytes"])
        path = config.dataset / "evidence/readback.json"
        content = path.read_text(); path.write_text(content.replace('"NOT_FOUND"', '"FOUND"'))
        changed = self.root / "changed"; predict(config.dataset, changed)
        with self.assertRaises(ValueError): compare_runs(before, changed, architectural=True)
        with self.assertRaises(ValueError): compare_runs(before, changed)
        reasons = {f"sample_{n}": "The direct synthetic readback changed from absence to presence." for n in range(32)}
        self.assertEqual(len(compare_runs(before, changed, explanations=reasons)["changed_predictions"]), 32)

    def test_frozen_source_tampering_is_rejected(self):
        config = self.sample_fixture(); run = self.root / "frozen"
        predict(config.dataset, run)
        (run / "source/main.py").write_bytes(b"tampered source")
        with self.assertRaises(ValueError): read_frozen(run)

    def test_evidence_gap_blocks_only_eligible_relevant_subjects(self):
        config = fixture(self.root); tools = default_tools(); inputs = tools.load(LoadInput(config))
        evidence = tools.extract(ExtractionInput(inputs, config.max_observations))
        source = inputs.artifacts[0]
        gap = EvidenceGap(source.file_id, "unresolved-document", source.captured_at,
                          (Identifier(IdentifierKind.EMAIL, "alpha@example.test"),))
        index = tools.index(IndexInput(inputs, replace(evidence, gaps=(gap,))))
        with self.assertRaises(AuditFailure) as caught:
            tools.investigate(InvestigationInput(inputs.requests[0], inputs, index))
        self.assertEqual(caught.exception.reason.value, "unrepresented_evidence")
        self.assertTrue(tools.investigate(InvestigationInput(inputs.requests[1], inputs, index)).authorized)
        original_index = tools.index(IndexInput(inputs, evidence))
        investigation = tools.investigate(InvestigationInput(inputs.requests[0], inputs, original_index))
        plan = tools.compile(CompilationInput(investigation))
        with self.assertRaises(AuditFailure):
            tools.validate(ValidationInput(replace(inputs, requests=inputs.requests[:1]), index, (investigation,), (plan,)))


if __name__ == "__main__": unittest.main()
