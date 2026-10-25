"""Allowlisted counts and fixed failure codes; no payloads, paths or errors."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Mapping
import json
import time
import uuid

from .contracts import AuditFailure, Effect, FailureType, Stage

COUNT_KEYS = frozenset({"requests", "identities", "activities", "artifacts", "observations",
                        "index_keys", "resources", "steps", "rows", "bytes", "external_calls",
                        "ownership_links", "inference_candidates", "assumptions", "evidence_gaps"})


@dataclass(frozen=True)
class ToolOutcome:
    tool: str
    outcome: str
    duration_ms: float
    counts: Mapping[str, int]
    failure_type: str | None = None


class Telemetry:
    """Sink and monotonic clock are injected; sink failures also abort the run."""

    def __init__(self, sink: Callable[[dict], None] | None = None,
                 clock: Callable[[], float] = time.perf_counter):
        self.sink = sink or (lambda event: None)
        self.clock = clock
        self.events: list[ToolOutcome] = []
        self.run_id = uuid.uuid4().hex
        self.run_failure: FailureType | None = None
        self.model_usage: dict | None = None

    def start(self) -> None:
        self.events.clear()
        self.run_id = uuid.uuid4().hex
        self.run_failure = None
        self.model_usage = None

    def record(self, stage: Stage, outcome: str, start: float,
               counts: Mapping[str, int], failure: FailureType | None = None) -> None:
        if (set(counts) - COUNT_KEYS or
                any(type(v) is not int or v < 0 for v in counts.values())):
            raise AuditFailure(FailureType.CONTRACT, stage)
        event = ToolOutcome(stage.value, outcome, round(max(0, self.clock() - start)*1000, 3),
                            dict(counts), failure.value if failure else None)
        self.events.append(event)
        self._emit({"event": "tool_outcome", **asdict(event)})

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        failures: dict[str, int] = {}
        durations: dict[str, float] = {}
        for event in self.events:
            durations[event.tool] = round(durations.get(event.tool, 0) + event.duration_ms, 3)
            if event.failure_type:
                failures[event.failure_type] = failures.get(event.failure_type, 0) + 1
            # Counts are stage-qualified to avoid counting rows at validation and
            # publication as two independent sets of requests.
            for name, value in event.counts.items():
                key = f"{event.tool}.{name}"
                counts[key] = counts.get(key, 0) + value
        if self.run_failure is not None and self.run_failure.value not in failures:
            failures[self.run_failure.value] = 1
        return {**({"inference_usage": self.model_usage} if self.model_usage is not None else {}),
                "tool_calls": len(self.events),
                "successful_calls": sum(e.outcome == "success" for e in self.events),
                "failure_types": failures, "counts": counts, "durations_ms": durations}

    def finish(self, success: bool, failure: FailureType | None = None) -> None:
        self.run_failure = failure
        self._emit({"event": "run_summary", "outcome": "success" if success else "failure",
                    **self.summary()})

    def _emit(self, event: dict) -> None:
        try:
            self.sink({"run_id": self.run_id, **event})
        except Exception:
            self.run_failure = FailureType.TELEMETRY
            raise AuditFailure(FailureType.TELEMETRY) from None


class JsonlSink:
    """Only Telemetry's allowlisted records should be passed to this sink."""

    permitted_effects = frozenset({Effect.WRITE_TELEMETRY})

    def __init__(self, path: Path):
        self.path = path

    def __call__(self, event: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")

