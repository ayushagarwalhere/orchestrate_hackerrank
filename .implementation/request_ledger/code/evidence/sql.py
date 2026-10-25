"""SQL snapshot evidence → Observations and account Coverage.

Each file runs in its own in-memory SQLite database (sources are never modified). Rows are observed at the
file's capture time (no row is newer than its file). Topology snapshots (files with a `Database topology`
header) that hold account profiles act as account Coverage: an account missing from every table is ABSENT
by omission. Inventory snapshots are never used for omission (sample case_04 cites evidence_54, not the
empty inventory evidence_90).
"""

import json
import re
import sqlite3

from evidence.common import files_under
from evidence.interpret import PROFILE, observe
from evidence.model import Coverage, link_keys_from, resource_prefix


def _rows(path):
    """Execute an export in a bounded in-memory database, never an attached file."""
    con = sqlite3.connect(":memory:")

    def authorize(action, arg1, arg2, database, trigger):
        if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_CREATE_VTABLE):
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_PRAGMA and (arg1 or "").lower() != "foreign_keys":
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in {"load_extension", "writefile", "readfile"}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    ticks = 0

    def limit_work():
        nonlocal ticks
        ticks += 1
        # Abort excessive SQL work instead of hanging on a malformed export.
        return int(ticks > 200)  # at most roughly two million VM instructions

    con.set_authorizer(authorize)
    con.set_progress_handler(limit_work, 10_000)
    try:
        con.executescript(path.read_text(encoding="utf-8"))
        con.row_factory = sqlite3.Row
        tables = [row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        data = {}
        for table in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            data[table] = [dict(row) for row in con.execute(f"SELECT * FROM {quoted} ORDER BY rowid")]
        return data
    finally:
        con.close()


def load(manifest, issues=None):
    observations, coverages = [], []
    for ef in files_under(manifest, "databases", {".sql"}):
        text = ef.path.read_text(encoding="utf-8")
        topology = re.search(r"^-- Database topology: (\S+)", text, re.M)
        ctx = dict(evidence_id=ef.file_id, file_captured_at=ef.captured_at, observed_at=ef.captured_at)
        accounts, profile_tables = set(), set()
        for table, rows in _rows(ef.path).items():
            if table == "snapshot_scope":
                continue
            for number, row in enumerate(rows, 1):
                record = dict(row)
                collection = table
                if "record_json" in record:
                    collection = record.get("collection_name") or table
                    record.update(json.loads(record.pop("record_json")))
                ctx["source"] = f"{ef.path.name}:{table}"
                ctx.update(location=f"table:{table}/row:{number}", physical_scope=(table,), time_basis="capture_time")
                found = observe(collection, record, ctx)
                observations.extend(found)
                if not found and issues is not None:
                    from evidence.ledger import ReferenceIssue
                    issues.append(ReferenceIssue(ef.file_id, ctx["location"], "unrecognized_record",
                        str(record.get("resource_id", "")), link_keys_from(record), ef.captured_at))
                if collection in PROFILE:
                    profile_tables.add(table)
                if resource_prefix(record.get("resource_id")) == "account":
                    accounts.add(record["resource_id"])
        if topology and profile_tables:
            coverages.append(Coverage(ef.file_id, ef.captured_at, ef.captured_at, "account_service",
                                      frozenset(accounts), "topology_table", f"{ef.path.name} ({topology.group(1)})",
                                      tuple(sorted(profile_tables))))
    return observations, coverages
