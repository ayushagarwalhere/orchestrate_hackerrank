"""Deterministic participant evidence adapters, independent of evaluation labels."""
from __future__ import annotations

from dataclasses import replace
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import struct
import subprocess
import tempfile

from .contracts import Artifact, timestamp
from .evidence import (Assumption, AssumptionCode, EvidenceBundle, EvidenceGap, EvidenceScope, FieldFact,
                       FieldPresence, Identifier, IdentifierKind, Observation, OwnershipLink,
                       Permission, PermissionFact, ScopeKind, State, reference_identifier)

COLLECTIONS = {
    "customer_profiles": ("account_service", "USER_PROFILE"),
    "customer_search_documents": ("search_service", "SEARCH_INDEX_ENTRY"),
    "search_documents_primary": ("search_service", "SEARCH_INDEX_ENTRY"),
    "customer_analytics_profiles": ("analytics_platform", "ANALYTICS_PROFILE"),
    "customer_analytics_reports": ("analytics_platform", "ANALYTICS_PROFILE"),
    "support_records": ("support_platform", "SUPPORT_MESSAGE"),
    "support_conversations": ("support_platform", "SUPPORT_MESSAGE"),
    "ticket_attachments": ("support_platform", "SUPPORT_ATTACHMENT"),
    "customer_exports": ("export_service", "USER_EXPORT"),
    "customer_export_jobs": ("export_service", "USER_EXPORT"),
    "connector_subscriptions": ("integration_service", "DATA_FLOW"),
    "connector_configurations": ("integration_service", "DATA_FLOW"),
    "backup_restore_entries": ("backup_service", "BACKUP_ARCHIVE"),
    "backup_catalog": ("backup_service", "BACKUP_ARCHIVE"),
    "security_audit_records": ("security_service", "SECURITY_AUDIT_LOG"),
    "security_audit_events": ("security_service", "SECURITY_AUDIT_LOG"),
    "deleted_customer_references": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "retained_order_records": ("legal_service", "LEGAL_HOLD_RECORD"),
}
DIRECT = {"name", "full_name", "display_name", "requester_name", "email", "requester_email",
          "owner_email", "customer_email", "phone", "owner_phone", "requester_phone", "email_hash"}
REFERENCES = {"customer_reference", "subject_reference", "subject_selector", "user_id", "owner_email",
              "email", "phone", "email_hash", "requester_email", "customer_email", "requester_phone", "owner_phone"}
RESULTS = {"FOUND": State.PRESENT, "NOT_FOUND": State.ABSENT, **{state.value: state for state in State}}


def merge(bundles):
    bundles = tuple(bundles)
    return EvidenceBundle(*(tuple(item for bundle in bundles for item in getattr(bundle, name))
        for name in ("observations", "ownership_links", "inference_candidates", "assumptions", "gaps")))


def leaves(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, key)
    elif isinstance(value, list):
        for item in value: yield from leaves(item, prefix)
    else:
        yield prefix, value


def boolean(value):
    if value is True or value in ("true", "1", 1): return True
    if value is False or value in ("false", "0", 0): return False
    return None


def record(artifact, system, category, raw, locator, observed, *, state=None, lookup=None,
           copy_id="logical", scope=EvidenceScope()):
    resource = raw["resource_id"]
    flat = list(leaves(raw))
    identifying = any(key in DIRECT and value not in (None, "", "null") for key, value in flat)
    attributable = identifying or any(key in {"user_id", "customer_reference", "subject_reference"}
                                      and value not in (None, "", "null") for key, value in flat)
    expected = {"enabled", "restore_allowed", "retention_until", "email", "phone", "email_hash", "customer_reference"}
    fields = tuple(FieldFact(key, FieldPresence.MISSING if key not in raw else
                            FieldPresence.NULL if raw[key] is None else FieldPresence.VALUE,
                            json.dumps(raw[key], sort_keys=True, ensure_ascii=False) if key in raw and raw[key] is not None else None)
                   for key in sorted(set(raw) | expected))
    conditions = []
    message = str(raw.get("message_text") or raw.get("message_excerpt") or "")
    # A delivery query contains fulfilment context even when an excerpt omits
    # the literal word 'order'. An explicit denial remains stronger than this
    # narrow textual predicate. A bare identity-only support row proves no
    # retained context.
    if category == "SUPPORT_MESSAGE" and (raw.get("shared_context") is True or
            raw.get("shared_context") is not False and re.search(
                r"\b(?:order|agent|another customer|delivery (?:query|issue|update)|shipment|invoice)\b",
                message, re.IGNORECASE)):
        conditions.append("shared_context")
    if category == "SUPPORT_ATTACHMENT" and raw.get("uploaded_by") == "customer":
        conditions.append("subject_only")
    if category == "ACCOUNT_TOMBSTONE" and str(raw.get("account_status", "")).upper() == "DELETED" and raw.get("subject_reference"):
        conditions.append("tombstone_reference_required")
    if category == "BACKUP_ARCHIVE" and boolean(raw.get("restore_allowed")) is not None:
        conditions.append("restore_blockable")
    if state is None:
        if category == "DATA_FLOW":
            enabled = boolean(raw.get("enabled"))
            state = State.UNKNOWN if enabled is None else State.ACTIVE if enabled else State.DISABLED
        elif category == "BACKUP_ARCHIVE":
            allowed = boolean(raw.get("restore_allowed"))
            state = State.UNKNOWN if allowed is None else State.ACTIVE if allowed else State.BLOCKED
        elif category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"}:
            complete = {"email", "phone", "email_hash", "customer_reference"} <= {key for key, _ in flat}
            state = State.IDENTIFIABLE if attributable else State.ANONYMIZED if complete else State.UNKNOWN
        elif category in {"SUPPORT_MESSAGE", "ACCOUNT_TOMBSTONE", "EMAIL_DELIVERY_LOG"}:
            complete = (bool(message) and {"requester_name", "requester_email", "requester_phone"} <= set(raw)
                        if category == "SUPPORT_MESSAGE" else False)
            state = State.IDENTIFIABLE if identifying else State.REDACTED if complete else State.UNKNOWN
        else:
            state = State.PRESENT
    permissions = tuple(PermissionFact(name, Permission.UNKNOWN if boolean(raw.get(name)) is None else
                        Permission.ALLOWED if boolean(raw[name]) else Permission.DENIED)
                        for name in ("enabled", "restore_allowed"))
    available = max(artifact.captured_at, observed)
    retention = raw.get("retention_until") or raw.get("retained_until")
    fact = Observation(artifact.file_id, locator, system, resource, category, state, artifact.captured_at,
        observed, available, copy_id, tuple(conditions), timestamp(retention) if retention else None,
        scope=scope, fields=fields, permissions=permissions)
    identifiers = []
    for key, value in flat:
        if key in REFERENCES and isinstance(value, str) and value and value != "null":
            if key == "email_hash": identifier = Identifier(IdentifierKind.EMAIL_HASH, value)
            elif "email" in key: identifier = Identifier(IdentifierKind.EMAIL, value)
            elif "phone" in key: identifier = Identifier(IdentifierKind.PHONE, value)
            else: identifier = reference_identifier(value)
            if identifier.kind is not IdentifierKind.UNKNOWN: identifiers.append(identifier)
    if isinstance(lookup, str) and lookup not in ("", "null"):
        identifier = reference_identifier(lookup)
        if identifier.kind is not IdentifierKind.UNKNOWN: identifiers.append(identifier)
    links = tuple(OwnershipLink(artifact.file_id, locator, system, resource, identifier,
                               artifact.captured_at, observed, available) for identifier in dict.fromkeys(identifiers))
    assumptions = (Assumption(AssumptionCode.LOGICAL_COPY_SCOPE, artifact.file_id, locator, fact.key),) if copy_id == "logical" else ()
    return EvidenceBundle((fact,), links, assumptions=assumptions)


def json_evidence(artifact):
    data = json.loads(artifact.content.decode("utf-8-sig"))
    output = []
    outer = timestamp(data.get("exported_at") or data.get("captured_at"))
    if "snapshots" in data:
        for n, snapshot in enumerate(data["snapshots"]):
            collection = snapshot["collection"]
            observed = timestamp(snapshot["captured_at"])
            for m, row in enumerate(snapshot["records"]):
                locator = f"/snapshots/{n}/records/{m}"
                if collection == "operational_record_history":
                    output.append(record(artifact, row["system"], row["record_type"], row, locator,
                        timestamp(row["recorded_at"]), state=RESULTS[row["result"]], lookup=row.get("lookup_value")))
                else:
                    system, category = COLLECTIONS[collection]
                    output.append(record(artifact, system, category, row, locator, observed))
    elif "service_exports" in data:
        names = {"profile_lookups": "USER_PROFILE", "index_queries": "SEARCH_INDEX_ENTRY",
                 "profiles": "ANALYTICS_PROFILE", "tickets": "SUPPORT_MESSAGE", "exports": "USER_EXPORT",
                 "connectors": "DATA_FLOW", "restore_entries": "BACKUP_ARCHIVE", "audit_records": "SECURITY_AUDIT_LOG"}
        for system, collections in data["service_exports"].items():
            for collection, rows in collections.items():
                for n, row in enumerate(rows):
                    body = dict(row); state = None; lookup = None
                    if collection == "profile_lookups":
                        body.update(row["profile"] or {})
                        state = State.ABSENT if row["status_code"] == 404 else State.PRESENT
                    elif collection == "index_queries":
                        lookup = row.get("query")
                        state = State.PRESENT if row["hits"] else State.ABSENT
                    output.append(record(artifact, system, names[collection], body,
                        f"/service_exports/{system}/{collection}/{n}", timestamp(row["observed_at"]), state=state, lookup=lookup))
    elif "collection" in data and "records" in data:
        system, category = COLLECTIONS[data["collection"]]
        for n, row in enumerate(data["records"]):
            output.append(record(artifact, system, category, row, f"/records/{n}", outer))
    else:
        raise ValueError("Unsupported JSON shape")
    result = merge(output)
    return replace(result, observations=tuple(replace(f, available_at=max(f.available_at, outer)) for f in result.observations),
                   ownership_links=tuple(replace(link, available_at=max(link.available_at, outer)) for link in result.ownership_links))


def sql_evidence(artifact):
    text = artifact.content.decode("utf-8-sig")
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    allowed = {sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_INSERT,
               sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT, sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_REINDEX}
    def authorize(action, first, second, database, trigger):
        if action in allowed or (action == sqlite3.SQLITE_UPDATE and first == "sqlite_master"):
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and second == "json_valid": return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_PRAGMA and first == "foreign_keys" and second == "ON": return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    connection.set_authorizer(authorize)
    ticks = [0]
    def progress():
        ticks[0] += 1
        return ticks[0] > 10000
    connection.set_progress_handler(progress, 1000)
    try:
        connection.executescript(text)
        tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        scopes = dict(connection.execute("SELECT origin_system,captured_at FROM snapshot_scope")) if "snapshot_scope" in tables else {}
        header = re.search(r"(?:Captured at:|snapshot_completed_at=)\s*(\S+)", text)
        observed_default = timestamp(header[1]) if header else artifact.captured_at
        output = []
        for table in tables:
            if table == "snapshot_scope": continue
            rows = [dict(r) for r in connection.execute('SELECT * FROM "' + table.replace('"','""') + '"')]
            if len(rows) > 100000: raise ValueError("Row bound")
            for n, row in enumerate(rows):
                if "record_json" in row:
                    body = json.loads(row["record_json"]); system, category = COLLECTIONS[row["collection_name"]]
                else:
                    body = row
                    collection = "customer_profiles" if table in {"customer_profiles_primary", "customer_profiles_failover_replica"} else table
                    system, category = COLLECTIONS[collection]
                observed = timestamp(scopes[system]) if system in scopes else observed_default
                copy = table if any(word in table for word in ("replica", "primary")) else "logical"
                output.append(record(artifact, system, category, body, f"table:{table}/row:{n}", observed,
                    copy_id=copy, scope=EvidenceScope(ScopeKind.DATABASE_QUERY, table, (table,))))
        return merge(output)
    finally:
        connection.close()


def log_fields(line):
    text = line.replace('\\"', '"').replace('\\"', '"')
    stamp = timestamp(text.split()[0])
    if re.match(r"^\S+\s+\{", text):
        row = json.loads(text[text.index("{"):])
    else:
        row = {}
        for match in re.finditer(r'([A-Za-z_][\w]*)=(?:"([^"]*)"|([^\s|]+))', text):
            value = match[2] if match[2] is not None else match[3]
            row[match[1]] = None if value == "null" else value
        if "[" in text and "event" not in row:
            m = re.match(r"^\S+\s+\[[^]]+\]\s+\[([^]]+)\]\s+\[([^]]+)\]\s+(\w+):", text)
            if m: row.update(service=m[1], trace_id=m[2], event=m[3])
        if "|" in text and "event" not in row:
            pieces = [s.strip() for s in text.split("|")]
            if len(pieces) >= 6: row.update(service=pieces[2], trace_id=pieces[3], event=pieces[4])
        if "<" in text and "service" not in row:
            m = re.match(r"^\S+\s+<\d+>1\s+\S+\s+(\S+)\s+(\S+)\s", text)
            if m: row.update(service=m[1], trace_id=m[2])
    row.setdefault("service", row.get("function") or row.get("logger"))
    return stamp, row


def log_evidence(artifact):
    output, traces = [], {}
    for number, line in enumerate(artifact.content.decode("utf-8-sig").splitlines(), 1):
        if not line.strip(): continue
        observed, row = log_fields(line)
        system = row.get("service"); event = row.get("event", "")
        trace = (system, row.get("trace_id") or row.get("requestId"))
        if event.endswith("_started") and trace[1]: traces[trace] = row
        if not row.get("resource_id"): continue
        start = traces.get(trace, {})
        lookup = next((source.get(k) for source in (row, start) for k in
            ("lookup_key", "match_key", "subject_key", "subject_ref", "scan_key", "correlation_key") if source.get(k)), None)
        category = None; state = None
        if event == "record_lookup":
            system, category, state = row["system"], row["record_type"], RESULTS[row["result"]]
        elif event == "profile_lookup_completed":
            category = "USER_PROFILE"
            state = State.ABSENT if str(row.get("rows")) == "0" or str(row.get("http_status")) == "404" else State.PRESENT
        elif event == "index_query_completed":
            category = "SEARCH_INDEX_ENTRY"
            state = State.ABSENT if row.get("result") in {"miss", "not_found"} or str(row.get("total_hits")) == "0" else State.PRESENT
        elif event in {"message_pii_scan", "message_read", "support_ticket_read_completed", "contact_query_completed", "contact_lookup_completed"}:
            system = "support_platform"; category = "SUPPORT_MESSAGE"
            if event in {"message_pii_scan", "message_read", "contact_query_completed", "contact_lookup_completed"}:
                state = State.IDENTIFIABLE if row.get("matched_value") or lookup or str(row.get("rows")) == "1" else State.UNKNOWN
        elif event == "attachment_pii_scan":
            category = "SUPPORT_ATTACHMENT"; state = State.PRESENT
        elif event in {"analytics_profile_read", "analytics_identity_scan", "analytics_profile_read_completed"}:
            category = "ANALYTICS_PROFILE"
            if row.get("matched_value"): row["email"] = row["matched_value"]
        elif event in {"connector_heartbeat", "connector_config_loaded", "connector_config_read_completed"}:
            category = "DATA_FLOW"
            if "enabled" not in row and row.get("status") == "active": row["enabled"] = True
        elif event in {"restore_candidate_evaluated", "restore_authorization_completed", "restore_policy_read_completed"}:
            category = "BACKUP_ARCHIVE"
        elif event in {"export_download_check_completed", "export_metadata_read_completed"}:
            category = "USER_EXPORT"; state = State.PRESENT
        elif event == "audit_record_read_completed":
            category = "SECURITY_AUDIT_LOG"; state = State.PRESENT
        if category:
            output.append(record(artifact, system, category, row, f"line:{number}", observed, state=state, lookup=lookup))
    return merge(output)


def image_text(artifact):
    if artifact.content[:8] != b"\x89PNG\r\n\x1a\n" or len(artifact.content) < 24: raise ValueError()
    width, height = struct.unpack(">II", artifact.content[16:24])
    if width < 10 or height < 10: raise ValueError()
    executable = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    if not executable.exists(): raise ValueError("Local OCR unavailable")
    source = Path(__file__).with_name("ocr.ps1").read_text(encoding="utf-8")
    scratch = Path(__file__).resolve().parents[2] / "runs" / ".ocr"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as directory:
        root = Path(directory).resolve()
        if not root.is_relative_to(scratch.resolve()): raise ValueError()
        path = root / "input.png"; path.write_bytes(artifact.content)
        command = "& { " + source + " } -ImagePath '" + str(path).replace("'", "''") + "'"
        result = subprocess.run([str(executable), "-NoProfile", "-NonInteractive", "-Command", command],
                                capture_output=True, timeout=30, check=True)
        if len(result.stdout) > 2_000_000: raise ValueError()
        return json.loads(result.stdout.decode("utf-8-sig"))


def media_evidence(artifact, known):
    if artifact.suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(artifact.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        lines = [{"text": line} for line in text.splitlines()]
    else:
        data = image_text(artifact); text, lines = data["text"], data["lines"]
    output = []
    # Ground resource naming in structured evidence, not request/case suffixes.
    resources = {fact.resource_id: (fact.system_id, fact.category) for fact in known}
    references = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]+|user_[0-9]+", text)
    for number, line in enumerate(lines):
        tokens = re.findall(r"\b(?:account|analytics|support|search|marketing|export|backup|data_flow|audit_record|tombstone)_[0-9]+\b", line["text"])
        for resource in tokens:
            if resource in resources:
                system, category = resources[resource]
            else:
                prefix = resource.rsplit("_", 1)[0]
                mapping = {"account": ("account_service", "USER_PROFILE"), "marketing": ("marketing_platform", "MARKETING_PROFILE"),
                    "support": ("support_platform", "SUPPORT_ATTACHMENT" if "ATTACHMENT" in text.upper() else "SUPPORT_MESSAGE"),
                    "search": ("search_service", "SEARCH_INDEX_ENTRY"), "analytics": ("analytics_platform", "ANALYTICS_PROFILE"),
                    "export": ("export_service", "USER_EXPORT"), "backup": ("backup_service", "BACKUP_ARCHIVE"),
                    "data_flow": ("integration_service", "DATA_FLOW"), "audit_record": ("security_service", "SECURITY_AUDIT_LOG")}
                if prefix not in mapping: continue
                system, category = mapping[prefix]
            # Table rows own only identifiers on their row; a selected details
            # header may link the document's single subject. Never cross-join a
            # multi-customer list with every identifier in the whole screenshot.
            local = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]+|user_[0-9]+", line["text"])
            owners = local or (references if len(set(references)) == 1 else [])
            raw = {"resource_id": resource, "document_text": text}
            if owners: raw["subject_reference"] = owners[0]
            state = State.UNKNOWN
            if artifact.suffix == ".pdf" and category == "SUPPORT_ATTACHMENT":
                state = State.PRESENT
                raw["owner_email"] = next((r for r in references if "@" in r), None)
            elif category in {"USER_PROFILE", "MARKETING_PROFILE", "USER_EXPORT", "SEARCH_INDEX_ENTRY"}:
                state = State.PRESENT
            output.append(record(artifact, system, category, raw, f"text-line:{number+1}", artifact.captured_at, state=state))
    result = merge(output)
    represented = {link.identifier.key for link in result.ownership_links}
    unrepresented = tuple(dict.fromkeys(reference_identifier(r) for r in references
                          if reference_identifier(r).key not in represented))
    # OCR/PDF without a grounded key cannot disappear as successful empty
    # extraction. Keep a subject-scoped coverage gap without inventing an ID.
    gaps = (EvidenceGap(artifact.file_id, "document", artifact.captured_at, unrepresented),) if unrepresented or not text.strip() else ()
    return replace(result, gaps=gaps)
