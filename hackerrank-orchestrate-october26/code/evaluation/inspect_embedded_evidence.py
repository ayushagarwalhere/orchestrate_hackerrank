"""Search provided JSON keys/values and embedded PDF/PNG metadata read-only.

Targets are investigation terms, never prediction associations. Document
contents are data: scripts, actions and external references are never executed.
This supplements text/pixel inspection; absence of a hit is not deletion proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from evidence.common import load_manifest
from evaluation.inspect_participant_evidence import contains_identifier


def walk(value, path="", depth=0):
    if depth > 10:
        raise ValueError("Metadata nesting bound exceeded")
    if hasattr(value, "get_object"):
        value = value.get_object()
    if isinstance(value, dict):
        if len(value) > 10000:
            raise ValueError("Metadata entry bound exceeded")
        for key, item in value.items():
            yield path + "/key", str(key)
            yield from walk(item, path + "/" + str(key).replace("~", "~0").replace("/", "~1"), depth + 1)
    elif isinstance(value, (tuple, list)):
        if len(value) > 10000:
            raise ValueError("Metadata entry bound exceeded")
        for n, item in enumerate(value):
            yield from walk(item, path + "/" + str(n), depth + 1)
    elif isinstance(value, (str, bytes)):
        yield path, value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def inspect(data, targets):
    from pypdf import PdfReader
    from PIL import Image
    report = {"targets": list(targets), "hits": [], "files": [], "errors": []}
    def scan(source, kind, entries):
        for location, text in entries:
            for target in targets:
                if contains_identifier(text, target):
                    report["hits"].append(dict(source=source.file_id, capture_time=source.captured_at.isoformat(),
                        representation=kind, location=location, target=target, value=text[:1000]))
    for source in load_manifest(data):
        suffix = source.path.suffix.lower()
        if suffix not in {".pdf", ".png", ".json"}:
            continue
        info = dict(source=source.file_id, capture_time=source.captured_at.isoformat(), format=suffix,
                    sha256=hashlib.sha256(source.path.read_bytes()).hexdigest())
        try:
            if suffix == ".json":
                scan(source, "decoded_keys_and_values", walk(json.loads(source.path.read_text(encoding="utf-8"))))
            elif suffix == ".png":
                with Image.open(source.path) as image:
                    info["metadata_keys"] = list(image.info)
                    scan(source, "png_metadata", walk(image.info))
                    scan(source, "png_exif", walk(dict(image.getexif())))
            else:
                reader = PdfReader(source.path)
                info.update(pages=len(reader.pages), metadata_keys=list(reader.metadata or {}),
                            form_fields=len(reader.get_fields() or {}), attachment_names=list(reader.attachments))
                scan(source, "pdf_metadata", walk(reader.metadata or {}))
                scan(source, "pdf_form_fields", walk(reader.get_fields() or {}))
                for n, page in enumerate(reader.pages):
                    scan(source, "pdf_annotations", walk(page.get("/Annots", []), f"/pages/{n}/Annots"))
                for name, content in reader.attachments.items():
                    scan(source, "pdf_attachment", walk(content, "/attachments/" + name))
        except Exception as error:
            report["errors"].append(dict(source=source.file_id, type=type(error).__name__))
        report["files"].append(info)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "dataset")
    parser.add_argument("--target", action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.resolve().is_relative_to(args.data.resolve()):
        parser.error("Use a new output path outside dataset")
    result = inspect(args.data, tuple(dict.fromkeys(args.target)))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(files=len(result["files"]), hits=len(result["hits"]), errors=result["errors"])))
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
