"""Build the code-only source ZIP for submission.

    uv run python code/package.py [--out code.zip]

Includes code/, a root setup README, requirements and evaluation reports. Excludes exploration scripts,
scratch caches, bytecode, environment files, the dataset, virtual environments, logs and prediction CSVs. Entries are
written in sorted order with a fixed timestamp so the archive is reproducible. Fails if a forbidden file
would be included, then prints the contents.
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_FILES = ["README.md", "requirements.txt"]
INCLUDE_DIRS = ["code"]
EXCLUDE = re.compile(r"(^|/)(__pycache__|\.pytest_cache|\.ruff_cache|\.venv|venv|node_modules)(/|$)|^code/(?:cache|explore)/|(^|/)\.env(?:\.[^/]*)?$|\.pyc$")
FORBIDDEN = re.compile(r"(^|/)\.env$|^dataset/|(^|/)(?:log\.txt|chat_transcript\.txt|outputs?\.csv)$|\.(zip|tar|gz|tgz|7z|rar)$")
SECRET = re.compile(rb"AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,}")
FIXED_TIME = (2026, 10, 25, 0, 0, 0)


def collect():
    files = [ROOT / f for f in INCLUDE_FILES if (ROOT / f).exists()]
    for d in INCLUDE_DIRS:
        files += [p for p in (ROOT / d).rglob("*") if p.is_file()]
    rel = sorted({p.relative_to(ROOT).as_posix() for p in files})
    return [r for r in rel if not EXCLUDE.search(r)]


def source_path(relative):
    # The release README is versioned. Repacking an extracted archive uses its
    # root README, so the resulting archive has the same layout and contents.
    path = ROOT / relative
    if relative == "README.md" and (ROOT / "SUBMISSION_README.md").is_file():
        path = ROOT / "SUBMISSION_README.md"
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Package source escapes project root")
    return path


def build(out):
    entries = collect()
    problems = [r for r in entries if FORBIDDEN.search(r)]
    problems += [r for r in entries if SECRET.search(source_path(r).read_bytes())]
    if problems:
        sys.exit(f"refusing to package forbidden or secret-bearing files: {problems}")
    out = Path(out)
    if out.resolve().is_relative_to((ROOT / "dataset").resolve()) or out.resolve().is_relative_to((ROOT / "code").resolve()):
        raise ValueError("Package output must be outside dataset and code")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in entries:
            info = zipfile.ZipInfo(rel, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, source_path(rel).read_bytes())
    return entries


def main():
    parser = argparse.ArgumentParser(description="Build code.zip")
    parser.add_argument("--out", default=str(ROOT / "code.zip"))
    args = parser.parse_args()
    entries = build(Path(args.out))
    size = Path(args.out).stat().st_size
    top = {}
    for e in entries:
        key = "/".join(e.split("/")[:2]) if e.count("/") else e
        top[key] = top.get(key, 0) + 1
    print(f"wrote {args.out}: {len(entries)} files, {size / 1024:.0f} KiB")
    for k, n in sorted(top.items()):
        print(f"  {n:4d}  {k}")


if __name__ == "__main__":
    main()
