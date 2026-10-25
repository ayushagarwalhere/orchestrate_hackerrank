"""Manifest access shared by the evidence loaders."""

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from identity import parse_ts


@dataclass(frozen=True)
class EvidenceFile:
    file_id: str
    path: Path
    origin: str
    captured_at: datetime


def load_manifest(data_dir):
    data_dir = Path(data_dir).resolve()
    evidence_dir = (data_dir / "evidence").resolve()
    with open(data_dir / "evidence_files.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    files, seen = [], set()
    for row in rows:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,127}", row["file_id"]):
            raise ValueError("Evidence source ID is not a safe identifier")
        path = (data_dir / row["file_path"]).resolve()
        # Resolve traversal and symlinks before granting a loader read access.
        if not path.is_relative_to(evidence_dir):
            raise ValueError("Evidence manifest path escapes dataset/evidence")
        if row["file_id"] in seen:
            raise ValueError("Evidence manifest contains duplicate file IDs")
        seen.add(row["file_id"])
        files.append(EvidenceFile(row["file_id"], path, row["origin"], parse_ts(row["captured_at"])))
    return files


def files_under(manifest, folder, suffixes):
    # Dispatch by declared file format, not an assumed directory spelling.
    # folder remains an API compatibility argument for existing adapters.
    return sorted((m for m in manifest if m.path.suffix.lower() in suffixes),
                  key=lambda m: m.file_id)
