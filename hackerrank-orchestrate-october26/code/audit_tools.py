"""Typed, narrow tools used by the audit coordinator.

These tools inspect local evidence and propose a plan. They have no capability
to execute that plan against production systems. Public reference answers belong
to evaluation/ and are deliberately absent from this interface.
"""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping, NamedTuple, Protocol

from evidence.index import EvidenceIndex, build
from image_extract import extract
from investigate import CaseInvestigation, investigate_all, load_requests
from policy import case_number, serialize, steps_for
from validate_output import validate


@dataclass(frozen=True)
class ToolContract:
    """Capabilities are declared here and attached to every run event."""

    purpose: str
    effects: tuple[str, ...] = ("read_dataset",)

    def __post_init__(self):
        if not self.purpose or type(self.effects) is not tuple or any(type(e) is not str for e in self.effects):
            raise ValueError("Invalid tool capability declaration")


@dataclass(frozen=True)
class AuditInputs:
    targets: tuple[Mapping[str, str], ...]
    requests: tuple[Mapping[str, str], ...]


class PredictionRow(NamedTuple):
    case_id: str
    deletion_status: str
    steps_json: str


class JsonModelPort(Protocol):
    """Models may return structured facts; they have no publication capability."""
    client: object | None

    def generate_json(self, task: str, prompt: str, prompt_version: str,
                      images=(), validate: Callable | None = None): ...


class AuditToolPort(Protocol):
    """Replaceable dependencies used by the actual coordinator."""
    contracts: Mapping[str, ToolContract]

    def load_inputs(self, data_dir: Path) -> AuditInputs: ...
    def extract_facts(self, data_dir: Path, llm: JsonModelPort | None) -> dict: ...
    def index_evidence(self, data_dir: Path) -> EvidenceIndex: ...
    def investigate(self, data_dir: Path, inputs: AuditInputs, index: EvidenceIndex,
                    llm: JsonModelPort | None) -> dict[str, CaseInvestigation]: ...
    def compile_plan(self, inputs: AuditInputs, cases: dict[str, CaseInvestigation]) -> list[PredictionRow]: ...
    def validate(self, candidate: Path, data_dir: Path) -> tuple[list[str], int]: ...


class AuditTools:
    """Dependency boundary: tests can replace tools without invoking a model."""

    contracts = MappingProxyType({
        "load_inputs": ToolContract("Load target and public-sample requests, never reference answers."),
        "extract_facts": ToolContract("Optional schema-checked image extraction.", ("read_dataset", "write_derived_cache", "model_api_if_enabled")),
        "index_evidence": ToolContract("Parse the corpus once and check image-extraction coverage.",
                                       ("read_dataset", "read_derived_cache", "write_rendered_review_images")),
        "investigate": ToolContract("Resolve identities, resource links and time-qualified states.",
                                    ("read_dataset", "write_derived_cache_if_enabled", "model_api_if_enabled")),
        "compile_plan": ToolContract("Render deterministic findings, remediation and verification.", ("pure_computation",)),
        "record_ledger": ToolContract("Explicit local export of facts and extraction accounting.", ("write_derived_ledger",)),
        "validate": ToolContract("Check a staged CSV against schema, citations, clocks and ordering.",
                                 ("read_dataset", "read_candidate")),
        "publish": ToolContract("Back up the previous output and atomically publish the validated CSV.", ("write_output", "write_backup")),
    })

    def load_inputs(self, data_dir: Path) -> AuditInputs:
        targets = tuple(MappingProxyType(row) for row in load_requests(data_dir, ("deletion_requests.csv",)))
        requests = tuple(MappingProxyType(row) for row in load_requests(data_dir))
        ids = [request["case_id"] for request in requests]
        if not targets or len(ids) != len(set(ids)):
            raise ValueError("Requests must be nonempty and case IDs unique across input files")
        return AuditInputs(targets, requests)

    def extract_facts(self, data_dir: Path, llm: JsonModelPort | None) -> dict:
        # The CLI constructs a live client only after explicit --enable-model.
        if llm is None or llm.client is None:
            return {}
        return extract(data_dir, llm)

    def index_evidence(self, data_dir: Path) -> EvidenceIndex:
        index = build(data_dir)
        # Missing extraction is a coverage failure, never a successful deletion.
        self.last_ledger = index.ledger
        index.ledger.assert_ready()
        return index

    def investigate(self, data_dir: Path, inputs: AuditInputs, index: EvidenceIndex, llm) -> dict[str, CaseInvestigation]:
        return investigate_all(data_dir, inputs.requests, index=index, llm=llm)

    def compile_plan(self, inputs: AuditInputs, cases: dict[str, CaseInvestigation]) -> list[PredictionRow]:
        # The model never chooses operation ordering or constructs final CSV rows.
        return [
            PredictionRow(request["case_id"], cases[request["case_id"]].status,
                          serialize(steps_for(cases[request["case_id"]])))
            for request in sorted(inputs.targets, key=lambda request: case_number(request["case_id"]))
        ]

    def validate(self, candidate: Path, data_dir: Path) -> tuple[list[str], int]:
        return validate(candidate, data_dir)
