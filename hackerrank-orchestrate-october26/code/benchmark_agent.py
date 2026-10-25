"""Bounded audit agent: observe -> investigate -> plan -> verify -> publish.

The fixed workflow is intentional. Evidence interpretation may use a model;
final state decisions, step ordering and publication use deterministic code.
There is one coordinator, not a simulated team of independent model agents.
"""

import csv
import hashlib
import os
import shutil
import tempfile
import time
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Callable, TypeVar

from audit_tools import AuditInputs, AuditToolPort, AuditTools, JsonModelPort, PredictionRow, ToolContract
from audit_artifacts import ValidatedCandidate, atomic_json, fingerprint

ROOT = Path(__file__).resolve().parents[1]
Result = TypeVar("Result")
HEADER = ("case_id", "deletion_status", "steps_json")


class RunState(str, Enum):
    CREATED = 'created'
    LOADED = 'loaded'
    EXTRACTED = 'extracted'
    INDEXED = 'indexed'
    INVESTIGATED = 'investigated'
    COMPILED = 'compiled'
    VALIDATED = 'validated'
    PUBLISHED = 'published'
    FAILED = 'failed'


TRANSITIONS = MappingProxyType({
    'load_inputs': (RunState.CREATED, RunState.LOADED),
    'extract_facts': (RunState.LOADED, RunState.EXTRACTED),
    'index_evidence': (RunState.EXTRACTED, RunState.INDEXED),
    'investigate': (RunState.INDEXED, RunState.INVESTIGATED),
    'compile_plan': (RunState.INVESTIGATED, RunState.COMPILED),
    'validate': (RunState.COMPILED, RunState.VALIDATED),
    'publish': (RunState.VALIDATED, RunState.PUBLISHED),
})


class ToolContractError(ValueError):
    """A dependency violated stage order, declared effects or return shape."""


def check_result(name: str, result) -> None:
    valid = True
    if name == 'load_inputs':
        valid = isinstance(result, AuditInputs) and bool(result.targets) and bool(result.requests)
    elif name == 'extract_facts':
        valid = isinstance(result, dict)
    elif name == 'index_evidence':
        valid = all(isinstance(getattr(result, attr, None), (list, tuple))
                    for attr in ('observations', 'coverages', 'activities'))
    elif name == 'investigate':
        valid = isinstance(result, dict)
    elif name == 'compile_plan':
        valid = isinstance(result, list) and all(isinstance(row, tuple) and len(row) == 3
                    and all(isinstance(value, str) for value in row) for row in result)
    else:
        valid = result is None
    if not valid:
        raise ToolContractError('Tool returned an invalid result shape')

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
    state: RunState = RunState.CREATED
    failure_type: str | None = None
    diagnostic_errors: list[str] = field(default_factory=list)

    def write(self, path: Path) -> None:
        # Aggregate telemetry excludes customer text, identifiers and credentials.
        atomic_json(path, asdict(self))


class OutputValidationError(ValueError):
    """A candidate was rejected before it could replace the published output."""


class AuditAgent:
    """A single-run coordinator with replaceable tools and an optional model port."""

    def __init__(self, tools: AuditToolPort | None = None, llm: JsonModelPort | None = None,
                 backup_dir: Path | None = None, *, clock: Callable[[], float] = time.perf_counter):
        self.tools = tools if tools is not None else AuditTools()
        self.llm = llm
        self.backup_dir = backup_dir if backup_dir is not None else ROOT / "archive/previous_outputs"
        self.trace = RunTrace(mode="live_enabled" if llm is not None else "offline")
        self.ledger = None
        self._clock = clock
        self._validated: ValidatedCandidate | None = None

    def _call(self, name: str, action: Callable[[], Result]) -> Result:
        """Record success/failure while preserving the original tool exception."""
        started = self._clock()
        error_type = None
        contract = None
        canonical = AuditTools.contracts.get(name)
        try:
            declared = getattr(self.tools, 'contracts', None)
            if not isinstance(declared, Mapping):
                raise ToolContractError('Tool capabilities are not declared')
            contract = declared.get(name)
            if not isinstance(contract, ToolContract) or canonical is None or contract.effects != canonical.effects:
                raise ToolContractError('Tool capabilities differ from the coordinator contract')
            if name == 'record_ledger':
                if self.trace.state not in (RunState.INDEXED, RunState.FAILED):
                    raise ToolContractError('Ledger export is out of order')
            elif name not in TRANSITIONS or self.trace.state != TRANSITIONS[name][0]:
                raise ToolContractError('Tool execution is out of order')
            result = action()
            check_result(name, result)
            if name in TRANSITIONS:
                self.trace.state = TRANSITIONS[name][1]
            return result
        except Exception as exc:
            # Exception messages may contain an email, document text or a key.
            # Traces retain the error class; callers can inspect errors locally.
            error_type = type(exc).__name__
            self.trace.state = RunState.FAILED
            self.trace.failure_type = self.trace.failure_type or error_type
            ledger = getattr(exc, "ledger", None)
            if ledger is not None:
                self.ledger = ledger
                self.trace.counts.update(ledger.summary())
            raise
        finally:
            self.trace.events.append(ToolEvent(
                name if canonical else 'unknown', canonical.effects if canonical else (),
                "failed" if error_type else "ok",
                round(max(0, self._clock() - started), 6), error_type,
            ))

    def _publish(self, candidate: Path, destination: Path) -> None:
        if self.trace.state is not RunState.VALIDATED or self._validated is None or not self._validated.matches(candidate):
            raise OutputValidationError('Publication requires the unchanged validated candidate')
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
        # A rejected new invocation must not expose a previous run's approval
        # or successful-publication state, including during path validation.
        self.trace = RunTrace(mode="live_enabled" if self.llm is not None else "offline")
        self.ledger = None
        self._validated = None
        data_dir, out_path = Path(data_dir).resolve(), Path(out_path).resolve()
        trace_path = Path(trace_path).resolve() if trace_path else None
        ledger_path = Path(ledger_path).resolve() if ledger_path else None
        if out_path.is_relative_to(data_dir):
            raise ValueError("Output must be outside the read-only dataset")
        if self.backup_dir.resolve().is_relative_to(data_dir):
            raise ValueError("Backup must be outside the read-only dataset")
        if trace_path and (trace_path.is_relative_to(data_dir) or trace_path == out_path):
            raise ValueError("Trace must be outside the dataset and separate from the CSV")
        if ledger_path and (ledger_path.is_relative_to(data_dir) or ledger_path in (out_path, trace_path)):
            raise ValueError("Ledger must be outside the dataset and separate from output and trace")

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
            def investigate_cases():
                result = self.tools.investigate(data_dir, inputs, index, self.llm)
                check_result('investigate', result)
                if set(result) != {request['case_id'] for request in inputs.requests}:
                    raise ToolContractError('Investigation returned incomplete case membership')
                return result
            cases = self._call("investigate", investigate_cases)
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
                stream.flush()
                os.fsync(stream.fileno())

            def validate_candidate() -> None:
                before = fingerprint(candidate)
                errors, count = self.tools.validate(candidate, data_dir)
                if not isinstance(errors, list) or type(count) is not int:
                    raise ToolContractError('Validator returned an invalid result shape')
                if errors or count != len(inputs.targets):
                    raise OutputValidationError(f"Candidate rejected: {len(errors)} validation error(s); {count} rows")
                if fingerprint(candidate) != before:
                    raise OutputValidationError('Validator modified the staged candidate')
                self._validated = ValidatedCandidate(candidate.resolve(), before, count)
                self.trace.counts["validated_rows"] = count

            self._call("validate", validate_candidate)
            self.trace.output_sha256 = self._validated.sha256
            # Requested diagnostics must be writable before committing the CSV.
            # A later telemetry failure cannot undo a completed publication.
            if trace_path:
                self.trace.write(trace_path)
            self._call("publish", lambda: self._publish(candidate, out_path))
            self.trace.counts.update({f"status_{status}": count for status, count in Counter(row[1] for row in rows).items()})
            return rows
        except Exception as exc:
            self.trace.state = RunState.FAILED
            self.trace.failure_type = self.trace.failure_type or type(exc).__name__
            if ledger_path and self.ledger is not None and not ledger_attempted:
                try:
                    self._call("record_ledger", lambda: self.ledger.write(ledger_path))
                except Exception:
                    self.trace.diagnostic_errors.append('ledger_write_failed')
            raise
        finally:
            if candidate is not None:
                try:
                    candidate.unlink(missing_ok=True)
                except OSError:
                    self.trace.diagnostic_errors.append('candidate_cleanup_failed')
            if trace_path:
                try:
                    self.trace.write(trace_path)
                except Exception:
                    self.trace.diagnostic_errors.append('trace_write_failed')
