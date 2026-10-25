"""JSON / TXT record evidence → Observations and account Coverage.

Families (data_notes §3.2): snapshot bundles, service resource exports, ledgers, single-collection exports,
and the shift-handover text. Record-level times (snapshot captured_at, observed_at, recorded_at) are kept
as `observed_at` for the two-clock rule. An explicitly empty account_service snapshot inside a bundle is
account Coverage (sample case_31 cites evidence_51).
"""

import json

from evidence.common import files_under
from evidence.interpret import observe
from evidence.model import Coverage, link_keys_from
from identity import parse_ts

SINGLE_COLLECTION_SYSTEM = {"customer_analytics_reports": "analytics_platform", "customer_export_jobs": "export_service"}


def _handover(ef, text, issues=None):
    out = []
    for number, line in enumerate(text.splitlines(), 1):
        parts = [p.strip() for p in line.lstrip("- ").split("|")]
        if not line.startswith("- ") or len(parts) != 6:
            if line.startswith("- ") and issues is not None:
                from evidence.ledger import ReferenceIssue
                issues.append(ReferenceIssue(ef.file_id, f"line:{number}", "unrecognized_text"))
            continue
        ts, system, rid, rtype, result, ident = parts
        record = {"resource_id": rid, "system": system, "record_type": rtype, "result": result,
                  "subject_reference": None if ident == "no direct identifier" else ident}
        ctx = dict(evidence_id=ef.file_id, file_captured_at=ef.captured_at, observed_at=parse_ts(ts),
                   source=f"{ef.path.name}:handover", location=f"line:{number}")
        out.extend(observe("handover_check", record, ctx))
    return out


def load(manifest, issues=None):
    observations, coverages = [], []
    for ef in files_under(manifest, "records", {".json", ".txt"}):
        text = ef.path.read_text(encoding="utf-8")
        if ef.path.suffix.lower() == ".txt":
            if not text.startswith("CUSTOMER PLATFORM - SHIFT HANDOVER"):
                raise ValueError("Unsupported text format")
            observations.extend(_handover(ef, text, issues))
            continue
        doc = json.loads(text)
        base = dict(evidence_id=ef.file_id, file_captured_at=ef.captured_at)
        def add(collection, record, ctx):
            found = observe(collection, record, ctx)
            observations.extend(found)
            if not found and issues is not None:
                from evidence.ledger import ReferenceIssue
                issues.append(ReferenceIssue(ef.file_id, ctx["location"], "unrecognized_record",
                    str(record.get("resource_id", "")), link_keys_from(record), ef.captured_at))
        if "snapshots" in doc:
            for n, snap in enumerate(doc["snapshots"]):
                seen = parse_ts(snap["captured_at"])
                if not snap["records"] and snap["data_store"] == "account_service" and snap["collection"] == "customer_profiles":
                    coverages.append(Coverage(ef.file_id, ef.captured_at, seen, "account_service", frozenset(),
                                              "empty_snapshot", f"{ef.path.name}:{snap['collection']}",
                                              (f"/snapshots/{n}/{snap['collection']}",)))
                for m, rec in enumerate(snap["records"]):
                    seen_rec = parse_ts(rec["recorded_at"]) if rec.get("recorded_at") else seen
                    ctx = dict(base, observed_at=seen_rec, source=f"{ef.path.name}:{snap['collection']}", location=f"/snapshots/{n}/records/{m}")
                    add(snap["collection"], rec, ctx)
        elif "service_exports" in doc:
            for system, collections in doc["service_exports"].items():
                for collection, rows in collections.items():
                    for n, rec in enumerate(rows):
                        ctx = dict(base, observed_at=parse_ts(rec["observed_at"]), system_hint=system,
                                   source=f"{ef.path.name}:{system}.{collection}", location=f"/service_exports/{system}/{collection}/{n}")
                        add(collection, rec, ctx)
        elif "record_count" in doc:
            if doc["record_count"] != len(doc["records"]): raise ValueError("Record count mismatch")
            for n, rec in enumerate(doc["records"]):
                ctx = dict(base, observed_at=parse_ts(rec["recorded_at"]), source=f"{ef.path.name}:ledger", location=f"/records/{n}")
                add("ledger", rec, ctx)
        else:
            seen = parse_ts(doc["captured_at"])
            for n, rec in enumerate(doc["records"]):
                ctx = dict(base, observed_at=seen, system_hint=SINGLE_COLLECTION_SYSTEM.get(doc["collection"]),
                           source=f"{ef.path.name}:{doc['collection']}", location=f"/records/{n}")
                add(doc["collection"], rec, ctx)
    return observations, coverages

