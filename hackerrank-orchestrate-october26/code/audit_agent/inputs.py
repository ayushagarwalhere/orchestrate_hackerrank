"""The only default audit tool that reads participant files."""
from __future__ import annotations

import csv
import hashlib
import io

from .contracts import (LOAD, Activity, Artifact, AuditFailure, Change, FailureType,
                        Identity, LoadInput, LoadedInputs, Request, Rule, timestamp)
from .evidence import Identifier, IdentifierKind

HEADERS = {
    "deletion_requests.csv": "case_id,email,requested_at,reported_status,reported_at,audit_at,request_text",
    "user_identities.csv": "user_id,name,email,phone,email_hash,updated_at",
    "user_audit_log.csv": "audit_id,user_id,event_time,field_name,old_value,new_value",
    "system_activity.csv": "activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details",
    "deletion_rules.csv": "rule_id,data_category,condition,required_action",
    "evidence_files.csv": "file_id,file_path,origin,captured_at",
}


class LoadInputs:
    contract = LOAD

    def __call__(self, value: LoadInput) -> LoadedInputs:
        try:
            return self._load(value)
        except AuditFailure:
            raise
        except Exception:
            raise AuditFailure(FailureType.INPUT) from None

    def _load(self, value: LoadInput) -> LoadedInputs:
        config = value.config
        if config.requests_file not in {"deletion_requests.csv", "sample_deletion_requests.csv"}:
            raise AuditFailure(FailureType.INPUT)
        dataset = config.dataset.resolve(strict=True)
        output = config.output.resolve()
        if (not dataset.is_dir() or output.is_relative_to(dataset) or output.suffix != ".csv" or
                any(type(n) is not int or n <= 0 for n in (
                    config.expected_cases, config.max_artifacts, config.max_file_bytes,
                    config.max_total_bytes, config.max_observations))):
            raise AuditFailure(FailureType.INPUT)
        total_bytes = 0

        def read(path):
            nonlocal total_bytes
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(dataset) or not resolved.is_file():
                raise AuditFailure(FailureType.INPUT)
            if resolved.stat().st_size > config.max_file_bytes:
                raise AuditFailure(FailureType.INPUT)
            with resolved.open("rb") as stream:
                content = stream.read(config.max_file_bytes + 1)
            total_bytes += len(content)
            if len(content) > config.max_file_bytes or total_bytes > config.max_total_bytes:
                raise AuditFailure(FailureType.INPUT)
            return content

        tables = {}
        for name, header in HEADERS.items():
            filename = config.requests_file if name == "deletion_requests.csv" else name
            reader = csv.DictReader(io.StringIO(read(dataset / filename).decode("utf-8-sig")))
            if reader.fieldnames != header.split(","):
                raise AuditFailure(FailureType.INPUT)
            rows = tuple(reader)
            if any(None in row or any(v is None for v in row.values()) for row in rows):
                raise AuditFailure(FailureType.INPUT)
            id_column = header.split(",")[0]
            ids = [r[id_column] for r in rows]
            if len(set(ids)) != len(ids) or any(not x.strip() for x in ids):
                raise AuditFailure(FailureType.INPUT)
            tables[name] = rows
        requests = tuple(Request(r["case_id"], r["email"], timestamp(r["requested_at"]),
                                 r["reported_status"], timestamp(r["reported_at"]),
                                 timestamp(r["audit_at"]), r["request_text"])
                         for r in tables["deletion_requests.csv"])
        if (len(requests) != config.expected_cases or any(
                not r.email.strip() or not r.request_text.strip() or r.requested_at > r.audit_at or
                r.reported_status not in {"COMPLETE", "PARTIALLY_COMPLETE", "NOT_STARTED"}
                for r in requests)):
            raise AuditFailure(FailureType.INPUT)
        identities = tuple(Identity(r["user_id"], tuple(Identifier(IdentifierKind(k), r[k]) for k in
                                    ("name", "email", "phone", "email_hash") if r[k].strip()),
                                    timestamp(r["updated_at"]))
                           for r in tables["user_identities.csv"])
        changes = tuple(Change(r["audit_id"], r["user_id"], timestamp(r["event_time"]),
                               r["field_name"], r["old_value"], r["new_value"])
                        for r in tables["user_audit_log.csv"])
        activities = tuple(Activity(r["activity_id"], timestamp(r["event_time"]), r["event_type"],
                                    r["source_system"], r["target_system"], r["resource_id"],
                                    r["reported_result"], r["details"])
                           for r in tables["system_activity.csv"])
        rules = tuple(Rule(r["rule_id"], r["data_category"], r["condition"], r["required_action"])
                      for r in tables["deletion_rules.csv"])
        if not rules or any(r.action not in {"DELETE", "REDACT", "ANONYMIZE", "RETAIN"}
                            or not r.category or not r.condition for r in rules):
            raise AuditFailure(FailureType.INPUT)
        manifest = tables["evidence_files.csv"]
        if not manifest or len(manifest) > config.max_artifacts:
            raise AuditFailure(FailureType.INPUT)
        artifacts = []
        seen_paths = set()
        for r in manifest:
            path = (dataset / r["file_path"]).resolve(strict=True)
            if not path.is_relative_to(dataset / "evidence") or path in seen_paths:
                raise AuditFailure(FailureType.INPUT)
            seen_paths.add(path)
            content = read(path)
            artifacts.append(Artifact(r["file_id"], path.suffix.lower(), timestamp(r["captured_at"]),
                                      content, hashlib.sha256(content).hexdigest()))
        actual = {p.resolve() for p in (dataset / "evidence").rglob("*") if p.is_file()}
        if actual != seen_paths:
            raise AuditFailure(FailureType.INPUT)
        return LoadedInputs(tuple(sorted(requests, key=lambda r: r.case_id)), identities,
                            changes, activities, rules, tuple(artifacts))
