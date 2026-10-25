"""Bounded audit agent: observe -> investigate -> plan -> verify -> publish.

The fixed workflow is intentional. Evidence interpretation may use a model;
final state decisions, step ordering and publication use deterministic code.
There is one coordinator, not a simulated team of independent model agents.
"""

import csv
import hashlib
import json
import os
import shutil
import tempfile
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, TypeVar

from audit_tools import AuditTools, PredictionRow

ROOT = Path(__file__).resolve().parents[1]
Result = TypeVar("Result")
HEADER = ("case_id", "deletion_status", "steps_json")

# These are disclosed limitations of the inherited scoring profile. An execution
# trace records them instead of describing heuristic ownership as proven fact.
ASSUMPTIONS = (
    "Inherited workflow timing and numeric case-order tie breaks",
    "Inherited account naming fallback and retrospective ownership membership",
    "Inherited authoritative coverage and persistent account-absence interpretation",
    "Inherited unknown-field defaults remain a policy interpretation limitation",
)


@dataclass(frozen=True)
class ToolEvent:
    tool: str
    effects: tuple[str, ...]
    outcome: str
    duration_seconds: float
    error_type: str | None = None


@dataclass
class RunTrace:
    """Execution evidence, not private reasoning or a reconstructed conversation."""

    mode: str
    events: list[ToolEvent] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    output_sha256: str | None = None
    published: bool = False
    assumptions: tuple[str, ...] = ASSUMPTIONS

    def write(self, path: Path) -> None:
        # Aggregate telemetry excludes customer text, identifiers and credentials.
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")


class OutputValidationError(ValueError):
    """A candidate was rejected before it could replace the published output."""


class AuditAgent:
    """A single-run coordinator with replaceable tools and an optional model port."""

    def __init__(self, tools: AuditTools | None = None, llm=None, backup_dir: Path | None = None):
        self.tools = tools if tools is not None else AuditTools()
        self.llm = llm
        self.backup_dir = backup_dir if backup_dir is not None else ROOT / "archive/previous_outputs"
        self.trace = RunTrace(mode="live_enabled" if llm is not None else "offline")
        self.ledger = None

    def _call(self, name: str, action: Callable[[], Result]) -> Result:
        """Record success/failure while preserving the original tool exception."""
        started = time.perf_counter()
        error_type = None
        try:
            return action()
        except Exception as exc:
            # Exception messages may contain an email, document text or a key.
            # Traces retain the error class; callers can inspect errors locally.
            error_type = type(exc).__name__
            ledger = getattr(exc, "ledger", None)
            if ledger is not None:
                self.ledger = ledger
                self.trace.counts.update(ledger.summary())
            raise
        finally:
            self.trace.events.append(ToolEvent(
                name, self.tools.contracts[name].effects,
                "failed" if error_type else "ok",
                round(time.perf_counter() - started, 6), error_type,
            ))

    def _publish(self, candidate: Path, destination: Path) -> None:
        if destination.exists():
            digest = hashlib.sha256(destination.read_bytes()).hexdigest()[:16]
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(destination, self.backup_dir / f"{destination.stem}-{digest}.csv")
        # Both paths are in the same directory/filesystem. Readers see the old
        # complete file or the new complete file, never a half-written CSV.
        os.replace(candidate, destination)
        self.trace.published = True

    def run(self, data_dir: Path, out_path: Path, trace_path: Path | None = None,
            ledger_path: Path | None = None) -> list[PredictionRow]:
        data_dir, out_path = Path(data_dir).resolve(), Path(out_path).resolve()
        trace_path = Path(trace_path).resolve() if trace_path else None
        ledger_path = Path(ledger_path).resolve() if ledger_path else None
        if out_path.is_relative_to(data_dir):
            raise ValueError("Output must be outside the read-only dataset")
        if trace_path and (trace_path.is_relative_to(data_dir) or trace_path == out_path):
            raise ValueError("Trace must be outside the dataset and separate from the CSV")
        if ledger_path and (ledger_path.is_relative_to(data_dir) or ledger_path in (out_path, trace_path)):
            raise ValueError("Ledger must be outside the dataset and separate from output and trace")

        # A coordinator can be reused, but each run has its own state and trace.
        self.trace = RunTrace(mode="live_enabled" if self.llm is not None else "offline")
        self.ledger = None
        candidate = None
        ledger_attempted = False
        try:
            inputs = self._call("load_inputs", lambda: self.tools.load_inputs(data_dir))
            self.trace.counts.update(targets=len(inputs.targets), requests=len(inputs.requests))
            self._call("extract_facts", lambda: self.tools.extract_facts(data_dir, self.llm))
            index = self._call("index_evidence", lambda: self.tools.index_evidence(data_dir))
            self.ledger = getattr(index, "ledger", None)
            if ledger_path and self.ledger is not None:
                ledger_attempted = True
                self._call("record_ledger", lambda: self.ledger.write(ledger_path))
            self.trace.counts.update(observations=len(index.observations), coverages=len(index.coverages),
                                     activities=len(index.activities))
            if getattr(index, "ledger", None) is not None:
                self.trace.counts.update(index.ledger.summary())
            cases = self._call("investigate", lambda: self.tools.investigate(data_dir, inputs, index, self.llm))
            resources = [resource for case in cases.values()
                         for resource in ([case.account] if case.account else []) + case.resources]
            self.trace.counts["unknown_resource_states"] = sum(resource.state is None for resource in resources)
            self.trace.counts["unresolved_case_references"] = sum(len(getattr(case, "unresolved_resources", ())) for case in cases.values())
            rows = self._call("compile_plan", lambda: self.tools.compile_plan(inputs, cases))

            # Write only a temporary candidate until the independent validator
            # checks all rows. A failed run leaves any previous output intact.
            out_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix=".audit-", suffix=".csv", dir=out_path.parent)
            candidate = Path(name)
            with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream, lineterminator="\n")
                writer.writerow(HEADER)
                writer.writerows(rows)

            def validate_candidate() -> None:
                errors, count = self.tools.validate(candidate, data_dir)
                if errors or count != len(inputs.targets):
                    raise OutputValidationError(f"Candidate rejected: {len(errors)} validation error(s); {count} rows")
                self.trace.counts["validated_rows"] = count

            self._call("validate", validate_candidate)
            self.trace.output_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
            self._call("publish", lambda: self._publish(candidate, out_path))
            self.trace.counts.update({f"status_{status}": count for status, count in Counter(row[1] for row in rows).items()})
            return rows
        except Exception:
            if ledger_path and self.ledger is not None and not ledger_attempted:
                self._call("record_ledger", lambda: self.ledger.write(ledger_path))
            raise
        finally:
            if candidate is not None:
                candidate.unlink(missing_ok=True)
            if trace_path:
                self.trace.write(trace_path)
