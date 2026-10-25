"""Independent synthetic fixtures; no public labels or organizer-only inputs."""
from __future__ import annotations

from dataclasses import replace
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit_agent import AuditAgent, AuditFailure, FailureType, RunConfig, default_tools
from audit_agent.contracts import (ArtifactExtraction, Effect, ExtractedEvidence, Observation, Stage, State,
                                   timestamp)
from audit_agent.inputs import HEADERS
from audit_agent.investigation import request_authorizes
from audit_agent.telemetry import Telemetry
from audit_agent.evidence import Identifier, IdentifierKind, OwnershipLink

AT = "2026-05-02T00:00:00Z"
BEFORE = "2026-05-01T00:00:00Z"
SECRET = "customer-text-and-provider-secret-MUST-NOT-LOG"


class Spy:
    def __init__(self, tool, callback=None):
        self.tool, self.contract, self.callback = tool, tool.contract, callback
        self.calls = []

    def __call__(self, value):
        self.calls.append(value)
        return self.callback(value) if self.callback else self.tool(value)


def fixture(root: Path, records=None, requests=None, extra_artifact=False) -> RunConfig:
    dataset = root / "dataset"
    (dataset / "evidence").mkdir(parents=True)
    if requests is None:
        requests = [
            ["case_a", "alpha@example.test", BEFORE, "COMPLETE", BEFORE, AT, "Please delete my account."],
            ["case_b", "beta@example.test", BEFORE, "NOT_STARTED", BEFORE, AT, "Please erase my account."],
            ["case_c", "gamma@example.test", BEFORE, "COMPLETE", BEFORE, AT,
             "Please export my account information. Do not delete my account."],
        ]
    if records is None:
        records = [
            dict(recorded_at=AT, system="account_service", resource_id="account_alpha", record_type="USER_PROFILE",
                 result="FOUND", subject_reference="alpha@example.test"),
            dict(recorded_at=AT, system="integration_service", resource_id="flow_alpha", record_type="DATA_FLOW",
                 result="ACTIVE", subject_reference="user_alpha"),
            dict(recorded_at=AT, system="security_service", resource_id="audit_alpha", record_type="SECURITY_AUDIT_LOG",
                 result="FOUND", subject_reference="user_alpha", retention_until="2027-01-01T00:00:00Z"),
            dict(recorded_at=AT, system="account_service", resource_id="account_beta", record_type="USER_PROFILE",
                 result="NOT_FOUND", subject_reference="beta@example.test"),
        ]
    document = {"exported_at": AT, "origin": "fixture_readback", "record_count": len(records), "records": records}
    (dataset / "evidence" / "readback.json").write_text(json.dumps(document), encoding="utf-8")
    tables = {
        "deletion_requests.csv": requests,
        "user_identities.csv": [
            ["user_alpha", "Alpha", "alpha@example.test", "", "", BEFORE],
            ["user_beta", "Beta", "beta@example.test", "", "", BEFORE]],
        "user_audit_log.csv": [], "system_activity.csv": [],
        "deletion_rules.csv": [
            ["rule_profile", "USER_PROFILE", "Always", "DELETE"],
            ["rule_security", "SECURITY_AUDIT_LOG", "Record is within the supplied retention period", "RETAIN"]],
        "evidence_files.csv": [["evidence_readback", "evidence/readback.json", "fixture", AT]],
    }
    if extra_artifact:
        (dataset / "evidence" / "needs-ocr.png").write_bytes(b"independent unsupported fixture")
        tables["evidence_files.csv"].append(["evidence_image", "evidence/needs-ocr.png", "fixture", AT])
    for name, rows in tables.items():
        with (dataset / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(HEADERS[name].split(","))
            writer.writerows(rows)
    return RunConfig(dataset, root / "output.csv", len(requests))


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[2] / ".test-runs"
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.root = Path(self.temp.name)
        if not self.root.resolve().is_relative_to(scratch.resolve()):
            raise RuntimeError("Temporary test directory escaped scratch root")
        self.addCleanup(self.temp.cleanup)
        self.events = []
        self.ticks = iter(n / 100 for n in range(1000))
        self.telemetry = Telemetry(self.events.append, lambda: next(self.ticks))

    def run_agent(self, config, tools=None):
        return AuditAgent(tools, self.telemetry).run(config)

    def assert_failure(self, config, kind, tools=None):
        config.output.write_bytes(b"previous validated output")
        with self.assertRaises(AuditFailure) as caught:
            self.run_agent(config, tools)
        self.assertEqual(caught.exception.kind, kind)
        self.assertEqual(config.output.read_bytes(), b"previous validated output")
        self.assertFalse(any(e.tool == Stage.PUBLISH.value for e in self.telemetry.events))
        self.assertEqual(self.events[-1]["event"], "run_summary")
        self.assertEqual(self.events[-1]["outcome"], "failure")

    def test_real_tools_end_to_end_three_cases(self):
        config = fixture(self.root)
        result = self.run_agent(config)
        rows = list(csv.DictReader(io.StringIO(config.output.read_text(encoding="utf-8"))))
        self.assertEqual(result.rows, 3)
        self.assertEqual([r["deletion_status"] for r in rows], ["INCOMPLETE", "COMPLETE", "NOT_APPLICABLE"])
        steps = json.loads(rows[0]["steps_json"])
        self.assertEqual([s["operation"] for s in steps], [
            "REPORT_REMAINING_RECORD", "REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "DELETE_RECORD",
            "VERIFY_RECORD_ABSENT", "VERIFY_RECORD_PRESENT", "VERIFY_DATA_FLOW_DISABLED"])
        self.assertEqual([s["step_no"] for s in steps], list(range(1, 8)))
        self.assertEqual(json.loads(rows[2]["steps_json"]), [])
        self.assertTrue(all(not s["evidence_id"] for s in steps if s["phase"] != "FINDING"))
        hand_authored = [
            ("FINDING", "account_service", "account_alpha", "REPORT_REMAINING_RECORD", "PRESENT", "evidence_readback"),
            ("FINDING", "integration_service", "flow_alpha", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", "evidence_readback"),
            ("REMEDIATION", "integration_service", "flow_alpha", "DISABLE_DATA_FLOW", "DISABLED", ""),
            ("REMEDIATION", "account_service", "account_alpha", "DELETE_RECORD", "ABSENT", ""),
            ("VERIFICATION", "account_service", "account_alpha", "VERIFY_RECORD_ABSENT", "ABSENT", ""),
            ("VERIFICATION", "security_service", "audit_alpha", "VERIFY_RECORD_PRESENT", "PRESENT", ""),
            ("VERIFICATION", "integration_service", "flow_alpha", "VERIFY_DATA_FLOW_DISABLED", "DISABLED", ""),
        ]
        expected_steps = [dict(zip(("phase", "system_id", "resource_id", "operation", "state", "evidence_id"), values),
                               step_no=n) for n, values in enumerate(hand_authored, 1)]
        self.assertEqual(steps, expected_steps)
        self.assertEqual(json.loads(rows[1]["steps_json"]), [{
            "step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_beta",
            "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_readback"}])
        self.assertEqual(self.events[-1]["counts"]["load_inputs.requests"], 3)
        self.assertTrue(all(e.duration_ms == 10 for e in self.telemetry.events))

    def test_index_built_once_and_identical_object_reused(self):
        tools = default_tools()
        index, investigate = Spy(tools.index), Spy(tools.investigate)
        self.run_agent(fixture(self.root), replace(tools, index=index, investigate=investigate))
        self.assertEqual(len(index.calls), 1)
        self.assertEqual(len(investigate.calls), 3)
        self.assertTrue(all(call.index is investigate.calls[0].index for call in investigate.calls))

    def test_optional_extraction_failure_never_publishes_or_logs_error_text(self):
        class FailingExtractor:
            def extract(self, artifact):
                raise RuntimeError(SECRET)
        config = fixture(self.root, extra_artifact=True)
        self.assert_failure(config, FailureType.PROVIDER, default_tools(FailingExtractor()))
        serialized = json.dumps(self.events)
        self.assertNotIn(SECRET, serialized)
        self.assertNotIn("alpha@example.test", serialized)
        self.assertNotIn("Please delete", serialized)
        self.assertNotIn(str(self.root).replace("\\", "\\\\"), serialized)
        failure = self.telemetry.events[-1]
        self.assertEqual(failure.counts["external_calls"], 1)
        self.assertEqual(failure.counts["artifacts"], 1)

    def test_unsupported_artifact_without_provider_blocks(self):
        self.assert_failure(fixture(self.root, extra_artifact=True), FailureType.UNSUPPORTED)

    def test_invalid_provider_result_blocks(self):
        class BadExtractor:
            def extract(self, artifact):
                return []  # Must be a tuple of typed facts, not an ignored empty result.
        self.assert_failure(fixture(self.root, extra_artifact=True), FailureType.MALFORMED,
                            default_tools(BadExtractor()))

    def test_optional_adapter_is_used_once_per_unsupported_file(self):
        class Extractor:
            calls = 0
            def extract(self, artifact):
                self.calls += 1
                facts = (Observation(artifact.file_id, "page:1/region:1", "account_service", "account_extra",
                                    "USER_PROFILE", State.PRESENT, artifact.captured_at, timestamp(AT), timestamp(AT)),)
                links = (OwnershipLink(artifact.file_id, "page:1/region:1", "account_service", "account_extra",
                    Identifier(IdentifierKind.EMAIL, "alpha@example.test"), artifact.captured_at, timestamp(AT), timestamp(AT)),)
                return ArtifactExtraction(artifact.file_id, artifact.sha256, facts, True, links)
        config = fixture(self.root, extra_artifact=True)
        extractor = Extractor()
        self.run_agent(config, default_tools(extractor))
        self.assertEqual(extractor.calls, 1)
        self.assertEqual(self.events[-1]["counts"]["extract_evidence.external_calls"], 1)

    def test_missing_manifest_coverage_from_replacement_cannot_publish(self):
        tools = default_tools()
        dropped = Spy(tools.extract, lambda value: ExtractedEvidence((), frozenset()))
        self.assert_failure(fixture(self.root), FailureType.INDEX, replace(tools, extract=dropped))

    def test_unknown_request_is_not_complete_or_not_applicable(self):
        request = [["case_unknown", "alpha@example.test", BEFORE, "COMPLETE", BEFORE, AT, "Review this, please."]]
        self.assert_failure(fixture(self.root, requests=request), FailureType.UNRESOLVED)

    def test_post_cutoff_evidence_cannot_prove_deletion(self):
        config = fixture(self.root)
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text())
        data["exported_at"] = "2026-05-03T00:00:00Z"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assert_failure(config, FailureType.UNRESOLVED)

    def test_equal_time_conflicting_reads_block(self):
        config = fixture(self.root)
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text())
        data["records"].append({**data["records"][0], "result": "NOT_FOUND"})
        data["record_count"] += 1
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assert_failure(config, FailureType.UNRESOLVED)

    def test_replica_present_is_not_erased_by_primary_absence(self):
        config = fixture(self.root)
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text())
        data["records"][0]["copy_id"] = "replica"
        data["records"].append({**data["records"][0], "copy_id": "primary", "result": "NOT_FOUND"})
        data["record_count"] += 1
        path.write_text(json.dumps(data), encoding="utf-8")
        self.run_agent(config)
        rows = list(csv.DictReader(io.StringIO(config.output.read_text(encoding="utf-8"))))
        self.assertEqual(rows[0]["deletion_status"], "INCOMPLETE")

    def test_missing_retained_record_blocks_unrepresentable_plan(self):
        config = fixture(self.root)
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text())
        data["records"][2]["result"] = "NOT_FOUND"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assert_failure(config, FailureType.POLICY)

    def test_dependency_inversion_blocks_plan(self):
        config = fixture(self.root)
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text())
        data["records"][0]["downstream"] = [["z_replica", "account_downstream"]]
        data["records"].append({**data["records"][0], "system": "z_replica",
                                "resource_id": "account_downstream", "downstream": []})
        data["record_count"] += 1
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assert_failure(config, FailureType.DEPENDENCY)

    def test_compiler_cannot_omit_required_verification(self):
        config, tools = fixture(self.root), default_tools()
        def omit(value):
            plan = tools.compile(value)
            return replace(plan, steps=plan.steps[:-1])
        self.assert_failure(config, FailureType.VALIDATION, replace(tools, compile=Spy(tools.compile, omit)))

    def test_compiler_cannot_invent_citation(self):
        config, tools = fixture(self.root), default_tools()
        def invent(value):
            plan = tools.compile(value)
            if not plan.steps:
                return plan
            return replace(plan, steps=(replace(plan.steps[0], evidence_id="invented"), *plan.steps[1:]))
        self.assert_failure(config, FailureType.VALIDATION, replace(tools, compile=Spy(tools.compile, invent)))

    def test_effect_contract_mismatch_is_rejected_before_tool_runs(self):
        config, tools = fixture(self.root), default_tools()
        invalid = Spy(tools.investigate)
        invalid.contract = replace(invalid.contract, permitted_effects=frozenset({Effect.WRITE_OUTPUT}))
        self.assert_failure(config, FailureType.CONTRACT, replace(tools, investigate=invalid))
        self.assertEqual(invalid.calls, [])

    def test_wrong_tool_output_type_is_rejected(self):
        config, tools = fixture(self.root), default_tools()
        broken = Spy(tools.extract, lambda value: None)
        self.assert_failure(config, FailureType.CONTRACT, replace(tools, extract=broken))

    def test_unexpected_tool_exception_is_sanitized(self):
        config, tools = fixture(self.root), default_tools()
        def crash(value):
            raise ValueError(SECRET)
        self.assert_failure(config, FailureType.INTERNAL, replace(tools, index=Spy(tools.index, crash)))
        self.assertNotIn(SECRET, json.dumps(self.events))

    def test_wrong_request_count_and_manifest_escape_block(self):
        config = fixture(self.root)
        self.assert_failure(replace(config, expected_cases=518), FailureType.INPUT)
        with (config.dataset / "evidence_files.csv").open("a", newline="") as stream:
            csv.writer(stream).writerow(["outside", "../../private.json", "bad", AT])
        self.assert_failure(config, FailureType.INPUT)

    def test_failed_atomic_replace_preserves_output_and_removes_temporary(self):
        config = fixture(self.root)
        config.output.write_bytes(b"previous validated output")
        with patch("audit_agent.output.os.replace", side_effect=OSError(SECRET)):
            with self.assertRaises(AuditFailure) as caught:
                self.run_agent(config)
        self.assertEqual(caught.exception.kind, FailureType.PUBLICATION)
        self.assertEqual(config.output.read_bytes(), b"previous validated output")
        self.assertEqual(list(self.root.glob(".audit-*.tmp")), [])
        self.assertNotIn(SECRET, json.dumps(self.events))

    def test_telemetry_failure_before_publication_blocks(self):
        config = fixture(self.root)
        def fail_sink(event):
            raise OSError(SECRET)
        config.output.write_bytes(b"previous validated output")
        with self.assertRaises(AuditFailure) as caught:
            AuditAgent(telemetry=Telemetry(fail_sink)).run(config)
        self.assertEqual(caught.exception.kind, FailureType.TELEMETRY)
        self.assertEqual(config.output.read_bytes(), b"previous validated output")

    def test_repeated_run_resets_telemetry_and_is_byte_stable(self):
        config = fixture(self.root)
        agent = AuditAgent(telemetry=self.telemetry)
        agent.run(config)
        first = config.output.read_bytes()
        first_count = self.telemetry.summary()["tool_calls"]
        first_id = self.telemetry.run_id
        agent.run(config)
        self.assertEqual(config.output.read_bytes(), first)
        self.assertEqual(self.telemetry.summary()["tool_calls"], first_count)
        self.assertNotEqual(self.telemetry.run_id, first_id)

    def test_cli_runs_real_coordinator_success_and_failure(self):
        config = fixture(self.root)
        cli = Path(__file__).resolve().parents[1] / "main.py"
        command = [sys.executable, "-B", str(cli), "--dataset", str(config.dataset), "--output", str(config.output),
                   "--telemetry", str(self.root / "telemetry.jsonl"), "--expected-cases", "3"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "published")
        before = config.output.read_bytes()
        (config.dataset / "evidence/readback.json").write_text("malformed " + SECRET)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stderr)["failure_type"], "extraction_invalid")
        self.assertNotIn(SECRET, result.stderr + result.stdout)
        self.assertEqual(config.output.read_bytes(), before)

    def test_cli_rejects_retired_unrestricted_extractor(self):
        config = fixture(self.root, extra_artifact=True)
        cli = Path(__file__).resolve().parents[1] / "main.py"
        log = self.root / "telemetry.jsonl"
        result = subprocess.run([sys.executable, "-B", str(cli), "--dataset", str(config.dataset),
                                 "--output", str(config.output), "--telemetry", str(log),
                                 "--expected-cases", "3", "--extractor", "missing_module:factory"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stderr)["failure_type"], "input_invalid")
        self.assertNotIn("missing_module", result.stderr)
        self.assertFalse(log.exists())
        self.assertFalse(config.output.exists())

    def test_request_negation_and_unknown_language_are_not_authorization(self):
        self.assertFalse(request_authorizes("Do not delete my account. Please export my data."))
        with self.assertRaises(AuditFailure):
            request_authorizes("Please delete my account only if the export succeeds.")
        with self.assertRaises(AuditFailure):
            request_authorizes("未知のリクエスト")
        with self.assertRaises(AuditFailure):
            request_authorizes('Please export the message "Please delete my account."')
        with self.assertRaises(AuditFailure):
            request_authorizes("Please erase my marketing profile permanently.")

    def test_partial_extraction_packet_blocks_publication(self):
        class PartialExtractor:
            def extract(self, artifact):
                return ArtifactExtraction(artifact.file_id, artifact.sha256, (), False)
        self.assert_failure(fixture(self.root, extra_artifact=True), FailureType.COVERAGE,
                            default_tools(PartialExtractor()))

    def test_extraction_packet_cannot_claim_another_artifact(self):
        class MisboundExtractor:
            def extract(self, artifact):
                return ArtifactExtraction("another_source", artifact.sha256, (), True)
        self.assert_failure(fixture(self.root, extra_artifact=True), FailureType.MALFORMED,
                            default_tools(MisboundExtractor()))

    def test_flow_is_disabled_before_its_dependent_record(self):
        config = fixture(self.root)
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text())
        data["records"][1]["downstream"] = [["account_service", "account_alpha"]]
        path.write_text(json.dumps(data), encoding="utf-8")
        self.run_agent(config)
        row = next(csv.DictReader(io.StringIO(config.output.read_text(encoding="utf-8"))))
        actions = [s["operation"] for s in json.loads(row["steps_json"]) if s["phase"] == "REMEDIATION"]
        self.assertEqual(actions, ["DISABLE_DATA_FLOW", "DELETE_RECORD"])

    def test_redacted_delete_required_record_still_requires_deletion(self):
        config = fixture(self.root)
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text())
        data["records"][0]["result"] = "REDACTED"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.run_agent(config)
        row = next(csv.DictReader(io.StringIO(config.output.read_text(encoding="utf-8"))))
        self.assertEqual(json.loads(row["steps_json"])[0]["operation"], "REPORT_REMAINING_RECORD")

    def test_eligible_historical_email_resolves_without_future_identity(self):
        config = fixture(self.root)
        path = config.dataset / "deletion_requests.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream))
        rows[1][1] = "old-alpha@example.test"
        with path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerows(rows)
        with (config.dataset / "user_audit_log.csv").open("a", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(["audit_email", "user_alpha", BEFORE, "email",
                                        "old-alpha@example.test", "alpha@example.test"])
        self.run_agent(config)

    def test_future_identity_snapshot_is_not_used_for_earlier_request(self):
        config = fixture(self.root)
        path = config.dataset / "user_identities.csv"
        path.write_text(path.read_text().replace(BEFORE, "2026-05-03T00:00:00Z"), encoding="utf-8")
        self.assert_failure(config, FailureType.UNRESOLVED)


if __name__ == "__main__":
    unittest.main()
