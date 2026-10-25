"""Source/ownership/state regressions, independent from challenge labels."""
from __future__ import annotations

from dataclasses import replace
import csv
import hashlib
import io
import json
import unittest

import test_workflow as workflow
from test_workflow import AT, BEFORE, Spy, fixture
from audit_agent import AuditFailure, FailureType, default_tools
from audit_agent.contracts import (ArtifactExtraction, ExtractionInput, IndexInput,
                                   InvestigationInput, LoadInput, timestamp)
from audit_agent.evidence import (AssumptionCode, EvidenceBundle, FieldPresence, Identifier, IdentifierKind,
                                  InferenceCandidate, InferenceKind, OwnershipLink, Permission, State)
from audit_agent.extraction import validate_bundle


class ExplicitEvidenceTests(unittest.TestCase):
    setUp = workflow.WorkflowTests.setUp
    run_agent = workflow.WorkflowTests.run_agent
    assert_failure = workflow.WorkflowTests.assert_failure

    def evidence(self, config, extractor=None):
        tools = default_tools(extractor)
        loaded = tools.load(LoadInput(config))
        extracted = tools.extract(ExtractionInput(loaded, config.max_observations))
        index = tools.index(IndexInput(loaded, extracted))
        return loaded, extracted, index

    def update(self, config, change):
        path = config.dataset / "evidence/readback.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        data["record_count"] = len(data["records"])
        path.write_text(json.dumps(data), encoding="utf-8")

    def only_alpha(self, records=None, extra_artifact=False):
        request = [["case_a", "alpha@example.test", BEFORE, "COMPLETE", BEFORE, AT,
                    "Please delete my account."]]
        return fixture(self.root, records=records, requests=request, extra_artifact=extra_artifact)

    def test_byte_identical_to_pre_refactor_fixture(self):
        config = fixture(self.root)
        self.run_agent(config)
        self.assertEqual(hashlib.sha256(config.output.read_bytes()).hexdigest(),
                         "7f9d5079d7299856e9c7ea89de1c9721bbe8148da35955c1451a42d3a010e315")

    def test_native_observations_and_ownership_are_separate(self):
        config = fixture(self.root)
        _, extracted, _ = self.evidence(config)
        self.assertEqual(len(extracted.observations), 4)
        self.assertEqual(len(extracted.ownership_links), 4)
        self.assertFalse(hasattr(extracted.observations[0], "subjects"))
        self.assertFalse(hasattr(extracted.ownership_links[0], "state"))
        for fact in extracted.observations:
            self.assertEqual(fact.source_id, "evidence_readback")
            self.assertEqual(fact.captured_at, timestamp(AT))
            self.assertIsInstance(fact.state, State)

    def test_current_state_citation_differs_from_ownership_source(self):
        config = self.only_alpha()
        self.update(config, lambda d: d.update(records=[{
            **d["records"][0], "recorded_at": BEFORE}]))
        path = config.dataset / "evidence/state.json"
        path.write_text(json.dumps({"exported_at": AT, "origin": "state_only", "record_count": 1,
            "records": [dict(recorded_at=AT, system="account_service", resource_id="account_alpha",
                             record_type="USER_PROFILE", result="NOT_FOUND")]}), encoding="utf-8")
        with (config.dataset / "evidence_files.csv").open("a", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(["evidence_state", "evidence/state.json", "state_only", AT])
        loaded, _, index = self.evidence(config)
        investigation = default_tools().investigate(InvestigationInput(loaded.requests[0], loaded, index))
        self.assertEqual({l.source_id for l in investigation.ownership_links}, {"evidence_readback"})
        self.assertEqual(investigation.resources[0].source_id, "evidence_state")
        self.run_agent(config)
        row = next(csv.DictReader(io.StringIO(config.output.read_text(encoding="utf-8"))))
        self.assertEqual(row["deletion_status"], "COMPLETE")
        self.assertEqual(json.loads(row["steps_json"])[0]["evidence_id"], "evidence_state")

    def test_catalog_ownership_alone_cannot_prove_absence(self):
        config = self.only_alpha(records=[])
        with (config.dataset / "system_activity.csv").open("a", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(["activity_owner", AT, "LINK_RESOURCE_IDENTITY", "catalog",
                "account_service", "account_alpha", "SUCCESS", "Linked alpha@example.test to user_alpha."])
        self.assert_failure(config, FailureType.UNRESOLVED)

    def test_state_without_ownership_does_not_infer_subject_from_resource_name(self):
        config = self.only_alpha()
        def remove_links(data):
            for record in data["records"]:
                record.pop("subject_reference", None)
        self.update(config, remove_links)
        self.assert_failure(config, FailureType.UNRESOLVED)

    def test_inference_candidate_never_replaces_direct_state(self):
        class CandidateExtractor:
            def extract(self, artifact):
                candidate = InferenceCandidate(InferenceKind.CARRY_FORWARD,
                    ("account_service", "account_alpha"), ((artifact.file_id, "page:1"),), State.ABSENT)
                return ArtifactExtraction(artifact.file_id, artifact.sha256, (), True,
                                          inference_candidates=(candidate,))
        config = self.only_alpha(extra_artifact=True)
        self.run_agent(config, default_tools(CandidateExtractor()))
        row = next(csv.DictReader(io.StringIO(config.output.read_text(encoding="utf-8"))))
        self.assertEqual(row["deletion_status"], "INCOMPLETE")
        self.assertEqual(json.loads(row["steps_json"])[0]["operation"], "REPORT_REMAINING_RECORD")

    def test_missing_null_and_false_permissions_remain_distinct(self):
        config = fixture(self.root)
        self.update(config, lambda d: d["records"][0].update(enabled=False, restore_allowed=None))
        _, extracted, _ = self.evidence(config)
        fact = extracted.observations[0]
        fields = {f.name: f for f in fact.fields}
        permissions = {p.name: p.value for p in fact.permissions}
        self.assertEqual(fields["enabled"].presence, FieldPresence.VALUE)
        self.assertEqual(fields["restore_allowed"].presence, FieldPresence.NULL)
        self.assertEqual(fields["copy_id"].presence, FieldPresence.MISSING)
        self.assertEqual(permissions, {"enabled": Permission.DENIED, "restore_allowed": Permission.UNKNOWN})
        self.assertTrue(all(p.value is Permission.UNKNOWN for p in extracted.observations[1].permissions))

    def test_missing_result_is_preserved_as_unknown_and_blocks_publication(self):
        config = fixture(self.root)
        self.update(config, lambda d: d["records"][0].pop("result"))
        _, extracted, _ = self.evidence(config)
        self.assertEqual(extracted.observations[0].state, State.UNKNOWN)
        result_field = next(f for f in extracted.observations[0].fields if f.name == "result")
        self.assertEqual(result_field.presence, FieldPresence.MISSING)
        self.assert_failure(config, FailureType.UNRESOLVED)

    def test_phone_formatting_matches_without_dropping_country_codes(self):
        config = self.only_alpha()
        identity_path = config.dataset / "user_identities.csv"
        with identity_path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream))
        rows[1][3] = "+91 20 1234 5678"
        with identity_path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerows(rows)
        with (config.dataset / "user_audit_log.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["audit_id", "user_id", "event_time", "field_name", "old_value", "new_value"])
            writer.writerow(["audit_phone", "user_alpha", BEFORE, "phone", "+44 20 1234 5678", "+91 20 1234 5678"])
        def records(data):
            original = {**data["records"][0], "subject_reference": "+44 (20) 1234-5678"}
            data["records"] = [original, {**original, "resource_id": "unrelated", "subject_reference": "+1 20 1234 5678"}]
        self.update(config, records)
        loaded, _, index = self.evidence(config)
        investigation = default_tools().investigate(InvestigationInput(loaded.requests[0], loaded, index))
        self.assertEqual([f.resource_id for f in investigation.resources], ["account_alpha"])
        phones = {link.identifier.raw for link in investigation.identity_links if link.identifier.kind is IdentifierKind.PHONE}
        self.assertEqual(phones, {"+44 20 1234 5678", "+91 20 1234 5678"})
        self.assertNotEqual(Identifier(IdentifierKind.PHONE, "+44 20 1234 5678").key,
                            Identifier(IdentifierKind.PHONE, "20 1234 5678").key)
        self.assertNotEqual(Identifier(IdentifierKind.PHONE, "+44 20 1234 5678").key,
                            Identifier(IdentifierKind.EMAIL, "+44 20 1234 5678").key)

    def test_negative_database_read_covers_only_queried_table(self):
        config = self.only_alpha()
        def records(data):
            old = {**data["records"][0], "recorded_at": BEFORE, "copy_id": "primary",
                   "scope": {"kind": "database_query", "table": "archive", "covered_tables": ["archive"]}}
            new = {**old, "recorded_at": AT, "result": "NOT_FOUND",
                   "scope": {"kind": "database_query", "table": "profiles", "covered_tables": ["profiles"]}}
            data["records"] = [old, new]
        self.update(config, records)
        loaded, _, index = self.evidence(config)
        investigation = default_tools().investigate(InvestigationInput(loaded.requests[0], loaded, index))
        self.assertEqual({(f.scope.table, f.state) for f in investigation.resources},
                         {("archive", State.PRESENT), ("profiles", State.ABSENT)})
        self.run_agent(config)
        row = next(csv.DictReader(io.StringIO(config.output.read_text(encoding="utf-8"))))
        self.assertEqual(row["deletion_status"], "INCOMPLETE")

    def test_uncovered_negative_database_table_is_invalid(self):
        config = self.only_alpha()
        self.update(config, lambda d: d["records"][0].update(result="NOT_FOUND",
            scope={"kind": "database_query", "table": "replica", "covered_tables": ["primary"]}))
        self.assert_failure(config, FailureType.MALFORMED)

    def test_retrospective_ownership_and_carry_forward_are_explicit_assumptions(self):
        class OwnerExtractor:
            def extract(self, artifact):
                link = OwnershipLink(artifact.file_id, "page:1", "account_service", "account_alpha",
                    Identifier(IdentifierKind.EMAIL, "alpha@example.test"), artifact.captured_at,
                    timestamp(AT), timestamp(AT))
                return ArtifactExtraction(artifact.file_id, artifact.sha256, (), True, (link,))
        config = self.only_alpha(extra_artifact=True)
        self.update(config, lambda d: d.update(records=[dict(recorded_at=BEFORE,
            system="account_service", resource_id="account_alpha", record_type="USER_PROFILE", result="NOT_FOUND")]))
        loaded, _, index = self.evidence(config, OwnerExtractor())
        investigation = default_tools().investigate(InvestigationInput(loaded.requests[0], loaded, index))
        self.assertEqual({c.kind for c in investigation.inference_candidates},
                         {InferenceKind.RETROSPECTIVE_LINK, InferenceKind.CARRY_FORWARD})
        self.assertTrue({AssumptionCode.RETROSPECTIVE_LINK, AssumptionCode.CARRY_FORWARD} <=
                         {a.code for a in investigation.assumptions})
        self.assertEqual(investigation.resources[0].observed_at, timestamp(BEFORE))

    def test_missing_capture_timestamp_is_rejected(self):
        config = fixture(self.root)
        loaded, extracted, _ = self.evidence(config)
        invalid = replace(extracted.observations[0], captured_at=None)
        with self.assertRaises(AuditFailure):
            validate_bundle(loaded.artifacts[0], EvidenceBundle((invalid,)))

    def test_forged_investigation_cannot_use_unowned_resource(self):
        config, tools = fixture(self.root), default_tools()
        def remove_proof(value):
            investigation = tools.investigate(value)
            return replace(investigation, ownership_links=()) if investigation.authorized else investigation
        self.assert_failure(config, FailureType.VALIDATION,
                            replace(tools, investigate=Spy(tools.investigate, remove_proof)))

    def test_future_ownership_does_not_link_an_earlier_state(self):
        class FutureOwnerExtractor:
            def extract(self, artifact):
                future = timestamp("2026-05-03T00:00:00Z")
                link = OwnershipLink(artifact.file_id, "page:1", "account_service", "account_alpha",
                    Identifier(IdentifierKind.EMAIL, "alpha@example.test"), artifact.captured_at, future, future)
                return ArtifactExtraction(artifact.file_id, artifact.sha256, (), True, (link,))
        config = self.only_alpha(extra_artifact=True)
        self.update(config, lambda d: d.update(records=[dict(recorded_at=BEFORE, system="account_service",
            resource_id="account_alpha", record_type="USER_PROFILE", result="NOT_FOUND")]))
        self.assert_failure(config, FailureType.UNRESOLVED, default_tools(FutureOwnerExtractor()))

    def test_names_are_preserved_but_not_used_as_unique_ownership(self):
        config = self.only_alpha()
        with (config.dataset / "user_audit_log.csv").open("a", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(["audit_name", "user_alpha", BEFORE, "name", "Former Alpha", "Alpha"])
        self.update(config, lambda d: d.update(records=[{**d["records"][0], "subject_reference": "Former Alpha"}]))
        loaded, extracted, _ = self.evidence(config)
        from audit_agent.identity import resolve_identity
        identity = resolve_identity(loaded.requests[0], loaded)
        self.assertEqual({link.identifier.raw for link in identity.links if link.identifier.kind is IdentifierKind.NAME},
                         {"Former Alpha", "Alpha"})
        self.assertEqual(extracted.inference_candidates[0].kind, InferenceKind.UNCLASSIFIED_REFERENCE)
        self.assertEqual(extracted.ownership_links, ())
        self.assert_failure(config, FailureType.UNRESOLVED)

    def test_future_candidates_and_assumptions_do_not_enter_case_trace(self):
        from audit_agent.evidence import Assumption
        class FutureMetadataExtractor:
            def extract(self, artifact):
                key = ("account_service", "account_alpha")
                candidate = InferenceCandidate(InferenceKind.CARRY_FORWARD, key,
                                                ((artifact.file_id, "page:1"),), State.ABSENT)
                assumption = Assumption(AssumptionCode.SUMMARY_READBACK, artifact.file_id, "page:1", key)
                return ArtifactExtraction(artifact.file_id, artifact.sha256, (), True,
                    inference_candidates=(candidate,), assumptions=(assumption,))
        config = self.only_alpha(extra_artifact=True)
        path = config.dataset / "evidence_files.csv"
        text = path.read_text(encoding="utf-8")
        text = text.replace("evidence_image,evidence/needs-ocr.png,fixture," + AT,
                            "evidence_image,evidence/needs-ocr.png,fixture,2026-05-03T00:00:00Z")
        path.write_text(text, encoding="utf-8")
        loaded, _, index = self.evidence(config, FutureMetadataExtractor())
        investigation = default_tools().investigate(InvestigationInput(loaded.requests[0], loaded, index))
        self.assertFalse(any(source == "evidence_image" for c in investigation.inference_candidates
                             for source, _ in c.support))
        self.assertFalse(any(a.source_id == "evidence_image" for a in investigation.assumptions))
