"""Read-only forensic search of participant sources, never answer fixtures.

Targets are search terms supplied on the CLI, not prediction associations.
Numeric suffix hits are reported separately and never establish ownership.
Images require visual review; the report does not pretend to OCR them.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from evidence.common import load_manifest

PARTICIPANT_CSVS = ("deletion_requests.csv", "sample_deletion_requests.csv", "user_identities.csv",
    "user_audit_log.csv", "system_activity.csv", "deletion_rules.csv", "evidence_files.csv")


def contains_identifier(text, target):
    """Exact token boundary; account_41 is not account_410 or account_41038."""
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(target) + r"(?![A-Za-z0-9_])", str(text)) is not None


def leaves(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from leaves(item, path + "/" + escaped)
    elif isinstance(value, list):
        for n, item in enumerate(value):
            yield from leaves(item, path + "/" + str(n))
    else:
        yield path or "/", value


def inspect_sql(path):
    """Inspect schemas, declared FKs and decoded rows in bounded memory only."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    def authorize(action, first, second, database, trigger):
        if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_CREATE_VTABLE): return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_PRAGMA and (first or "").lower() not in {"foreign_keys", "foreign_key_list", "table_info"}: return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and (second or "").lower() in {"load_extension", "readfile", "writefile"}: return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    con.set_authorizer(authorize)
    ticks = 0
    def bounded():
        nonlocal ticks
        ticks += 1
        return int(ticks > 200)
    con.set_progress_handler(bounded, 10000)
    try:
        con.executescript(Path(path).read_text(encoding="utf-8"))
        names = [r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        tables = []
        for name in names:
            quoted = '"' + name.replace('"', '""') + '"'
            tables.append({"table": name,
                "columns": [dict(r) for r in con.execute("PRAGMA table_info(" + quoted + ")")],
                "foreign_keys": [dict(r) for r in con.execute("PRAGMA foreign_key_list(" + quoted + ")")],
                "rows": [dict(r) for r in con.execute("SELECT * FROM " + quoted)]})
        return tables
    finally:
        con.close()


def inspect_corpus(data_dir, targets, render_dir=None):
    data_dir = Path(data_dir).resolve()
    manifest = load_manifest(data_dir)
    targets = tuple(dict.fromkeys(targets))
    numeric = {t: t.rsplit("_", 1)[-1] for t in targets if re.search(r"_\d+$", t)}
    report = {"targets": targets, "exact_hits": [], "numeric_hits": [], "normalized_hits": [],
        "files": [], "sql_catalog": [], "visual_sources": [], "errors": [],
        "excluded": ["sample_output.csv", "output.csv", "evaluation fixtures", "organizer/generator files"],
        "numeric_hits_establish_ownership": False}

    def scan(source_id, location, value, captured_at=None, representation="text"):
        text = str(value)
        base = {"source_id": source_id, "location": location, "captured_at": captured_at, "representation": representation}
        for target in targets:
            if contains_identifier(text, target):
                report["exact_hits"].append(dict(base, target=target, value=value))
            normalized = unicodedata.normalize("NFKC", text)
            if normalized != text and contains_identifier(normalized, target):
                report["normalized_hits"].append(dict(base, target=target, value=value))
        for target, number in numeric.items():
            if contains_identifier(text, number):
                report["numeric_hits"].append(dict(base, target=target, value=value))

    for name in PARTICIPANT_CSVS:
        path = data_dir / name
        if not path.exists(): continue
        report["files"].append({"source_id": name, "path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1): scan(name, f"line:{number}", line)
        with path.open(encoding="utf-8", newline="") as stream:
            for n, row in enumerate(csv.DictReader(stream), 1):
                for pointer, value in leaves(row): scan(name, f"row:{n}" + pointer, value, representation="csv")
    for source in manifest:
        cap = source.captured_at.isoformat(); suffix = source.path.suffix.lower()
        info = {"source_id": source.file_id, "path": str(source.path.relative_to(data_dir)).replace("\\", "/"), "captured_at": cap}
        try:
            info["sha256"] = hashlib.sha256(source.path.read_bytes()).hexdigest()
            if suffix in {".sql", ".json", ".txt", ".log"}:
                for n, line in enumerate(source.path.read_text(encoding="utf-8").splitlines(), 1): scan(source.file_id, f"line:{n}", line, cap)
            if suffix == ".json":
                for pointer, value in leaves(json.loads(source.path.read_text(encoding="utf-8"))): scan(source.file_id, pointer, value, cap, "decoded_json")
            elif suffix == ".sql":
                tables = inspect_sql(source.path)
                report["sql_catalog"].append({"source_id": source.file_id, "captured_at": cap,
                    "tables": [{"table": t["table"], "columns": t["columns"], "foreign_keys": t["foreign_keys"], "row_count": len(t["rows"])} for t in tables]})
                for table in tables:
                    for n, row in enumerate(table["rows"], 1):
                        for column, value in row.items():
                            location = f"table:{table['table']}/row:{n}/{column}"
                            scan(source.file_id, location, value, cap, "sql_value")
                            if isinstance(value, str) and value.lstrip().startswith(("{", "[")):
                                try: decoded = json.loads(value)
                                except ValueError: continue
                                for pointer, leaf in leaves(decoded): scan(source.file_id, location + pointer, leaf, cap, "decoded_sql_json")
            elif suffix == ".pdf":
                import pdfplumber
                with pdfplumber.open(source.path) as pdf:
                    info["pages"] = len(pdf.pages)
                    for n, page in enumerate(pdf.pages, 1):
                        text = page.extract_text() or ""
                        for line, value in enumerate(text.splitlines(), 1): scan(source.file_id, f"page:{n}/line:{line}", value, cap, "pdf_text")
                        rendered = None
                        if render_dir is not None:
                            destination = Path(render_dir).resolve()
                            if destination.is_relative_to(data_dir): raise ValueError("Render output must be outside dataset")
                            destination.mkdir(parents=True, exist_ok=True)
                            rendered = destination / f"{source.file_id}-page-{n}.png"
                            page.to_image(resolution=120).save(rendered, format="PNG")
                        report["visual_sources"].append(dict(info, page=n, rendered=str(rendered) if rendered else None))
            elif suffix in {".png", ".jpg", ".jpeg"}:
                report["visual_sources"].append(dict(info, original=str(source.path), review="manual_pixel_review_required"))
        except Exception as error:
            report["errors"].append({"source_id": source.file_id, "error_type": type(error).__name__})
        report["files"].append(info)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "dataset")
    parser.add_argument("--target", action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path)
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(args.data.resolve()) or args.out.exists():
        parser.error("Use a new output path outside dataset")
    report = inspect_corpus(args.data, args.target, args.render_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(report["files"]), "exact_hits": len(report["exact_hits"]),
        "numeric_hits": len(report["numeric_hits"]), "errors": len(report["errors"]),
        "visual_sources": len(report["visual_sources"])}))


if __name__ == "__main__": main()
