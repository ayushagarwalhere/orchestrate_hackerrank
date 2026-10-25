"""Extraction accounting is separate from resource state and policy findings."""
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time


class ExtractionStatus(str, Enum):
    PROCESSED = "PROCESSED"
    EMPTY = "EMPTY"  # Inspected zero rows; not an absence observation.
    FAILED = "FAILED"
    MISSING = "MISSING"
    UNSUPPORTED = "UNSUPPORTED"
    REVIEW = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class ReferenceIssue:
    source_id: str
    location: str
    reason: str
    reference: str = field(default="", repr=False)
    identifying_keys: frozenset = field(default_factory=frozenset, repr=False)
    captured_at: datetime | None = None
    identifying_fields: tuple = field(default_factory=tuple, repr=False)


@dataclass(frozen=True)
class FileExtraction:
    source_id: str
    format: str
    captured_at: datetime
    content_sha256: str | None
    status: ExtractionStatus
    observation_count: int
    coverage_count: int
    duration_seconds: float
    failure_type: str | None = None
    systems: tuple[str, ...] = ()


class EvidenceCoverageError(ValueError):
    def __init__(self, ledger):
        self.ledger = ledger
        super().__init__("Evidence extraction is incomplete; inspect the ledger")


class EvidenceResolutionError(ValueError):
    """Extracted facts do not establish a required resource state."""


@dataclass(frozen=True)
class EvidenceLedger:
    files: tuple[FileExtraction, ...]
    unresolved_references: tuple[ReferenceIssue, ...]
    observations: tuple = ()
    coverages: tuple = ()

    def write(self, path):
        """Explicit local export; unlike telemetry this contains source facts."""
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        def encode(value):
            if isinstance(value, datetime): return value.isoformat()
            if isinstance(value, Enum): return value.value
            if isinstance(value, (set, frozenset)): return sorted(value)
            raise TypeError("Unsupported ledger value")
        content = json.dumps({"schema_version": "evidence-ledger/v1", **asdict(self)}, default=encode, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        descriptor, name = tempfile.mkstemp(prefix=".ledger-", suffix=".json", dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @property
    def extraction_failures(self):
        return tuple(f for f in self.files if f.status is ExtractionStatus.FAILED)

    @property
    def missing_extraction(self):
        return tuple(f for f in self.files if f.status in {ExtractionStatus.MISSING, ExtractionStatus.UNSUPPORTED})

    @property
    def files_processed(self):
        return tuple(f for f in self.files if f.status in {ExtractionStatus.PROCESSED, ExtractionStatus.EMPTY})

    @property
    def system_coverage(self):
        # Files observed per system, never a claim that every system/store was
        # exhaustively queried. Snapshot scopes are a separate typed structure.
        return {system: tuple(f.source_id for f in self.files if system in f.systems)
                for system in sorted({system for f in self.files for system in f.systems})}

    def assert_ready(self):
        if any(f.status not in {ExtractionStatus.PROCESSED, ExtractionStatus.EMPTY} for f in self.files):
            raise EvidenceCoverageError(self)

    def summary(self):
        counts = Counter(f.status.value for f in self.files)
        return {"files_manifest": len(self.files), "files_processed": len(self.files_processed),
                "extraction_failures": len(self.extraction_failures), "missing_extraction": len(self.missing_extraction),
                "visual_or_parse_review": counts[ExtractionStatus.REVIEW.value],
                "empty_extractions": counts[ExtractionStatus.EMPTY.value],
                "unresolved_references": len(self.unresolved_references), "systems_observed": len(self.system_coverage)}


def extract_corpus(manifest, links, facts_dir, visual_reader=None, render_dir=None, clock=time.perf_counter):
    """Parse each source once; keep every source outcome even after failures."""
    from evidence import documents, images, logs, records, sql
    from evidence.model import State
    observations, coverages, outcomes, issues, missing = [], [], [], [], []
    for source in manifest:
        started = clock(); digest = None; local_obs, local_cov, local_issues = [], [], []
        status, failure = ExtractionStatus.EMPTY, None
        try:
            digest = hashlib.sha256(source.path.read_bytes()).hexdigest()
            suffix = source.path.suffix.lower()
            if suffix == ".sql":
                local_obs, local_cov = sql.load([source], issues=local_issues)
            elif suffix in {".json", ".txt"}:
                local_obs, local_cov = records.load([source], issues=local_issues)
            elif suffix == ".log":
                local_obs = logs.load([source], issues=local_issues)
            elif suffix == ".pdf":
                local_obs = documents.load([source], links, issues=local_issues,
                    visual_reader=visual_reader, render_dir=render_dir)
            elif suffix in {".png", ".jpg", ".jpeg"}:
                local_obs, absent = images.load([source], facts_dir, links, issues=local_issues)
                if absent:
                    missing.extend(absent); status = ExtractionStatus.MISSING; failure = "screenshot_extraction_missing"
            else:
                status = ExtractionStatus.UNSUPPORTED; failure = "unsupported_format"
            if status is ExtractionStatus.EMPTY:
                status = ExtractionStatus.PROCESSED if local_obs or local_cov else ExtractionStatus.EMPTY
            if any(i.reason in {
                    "visual_review_required", "invalid_image_record", "unrecognized_record", "unparsed_log", "unrecognized_text"} for i in local_issues):
                status = ExtractionStatus.REVIEW; failure = "unresolved_extraction"
            if any(o.category is None for o in local_obs):
                status = ExtractionStatus.REVIEW; failure = "unclassified_category"
        except FileNotFoundError:
            status = ExtractionStatus.MISSING; failure = "source_missing"
        except Exception as error:
            # Do not store exception strings, paths, text or provider credentials.
            status = ExtractionStatus.FAILED; failure = type(error).__name__
            local_obs, local_cov = [], []
        observations.extend(local_obs); coverages.extend(local_cov); issues.extend(local_issues)
        outcomes.append(FileExtraction(source.file_id, source.path.suffix.lower(), source.captured_at, digest, status,
            len(local_obs), len(local_cov), round(max(0, clock() - started), 6), failure,
            tuple(sorted({o.system_id for o in local_obs} | {c.system_id for c in local_cov}))))
    known = {o.resource_id for o in observations}
    issues.extend(ReferenceIssue(o.source_id, o.source_location or o.source, "resource_reference", reference,
                                o.link_keys, o.file_captured_at)
                  for o in observations for reference in sorted(o.refs - known))
    return observations, coverages, missing, EvidenceLedger(tuple(outcomes), tuple(issues), tuple(observations), tuple(coverages))
