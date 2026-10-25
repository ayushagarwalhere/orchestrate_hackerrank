"""Typed stage boundaries. Sensitive payloads never belong in telemetry."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Generic, Mapping, Protocol, TypeVar
import unicodedata

from .evidence import (Assumption, EvidenceGap, Identifier, IdentityLink, InferenceCandidate, ModelProvenance,
                       Observation, OwnershipLink, State)


class Effect(str, Enum):
    READ_DATASET = "read_dataset"
    EXTERNAL_EXTRACTION = "external_extraction"
    WRITE_OUTPUT = "write_output"
    WRITE_TELEMETRY = "write_telemetry"
    READ_CACHE = "read_cache"
    WRITE_CACHE = "write_cache"
    WRITE_TEMP = "write_temp"


class Stage(str, Enum):
    LOAD = "load_inputs"
    EXTRACT = "extract_evidence"
    INDEX = "index_evidence"
    INVESTIGATE = "investigate"
    COMPILE = "compile_plan"
    VALIDATE = "validate_output"
    PUBLISH = "publish_output"


class FailureType(str, Enum):
    INPUT = "input_invalid"
    EXTRACTION = "extraction_failed"
    UNSUPPORTED = "extraction_unsupported"
    MALFORMED = "extraction_invalid"
    PROVIDER = "extraction_provider_failed"
    COVERAGE = "extraction_incomplete"
    INDEX = "index_invalid"
    UNRESOLVED = "investigation_unresolved"
    POLICY = "policy_unresolved"
    DEPENDENCY = "dependency_conflict"
    VALIDATION = "output_invalid"
    PUBLICATION = "publication_failed"
    TELEMETRY = "telemetry_failed"
    CONTRACT = "tool_contract_invalid"
    INTERNAL = "internal_error"
    LIVE_DISABLED = "live_inference_disabled"
    MODEL_BUDGET = "model_budget_exhausted"
    MODEL_TIMEOUT = "model_timeout"
    MODEL_RESPONSE = "model_response_invalid"
    MODEL_USAGE = "model_usage_unknown"
    CACHE = "model_cache_invalid"


class FailureReason(str, Enum):
    INTENT = "request_intent"
    IDENTITY = "identity_resolution"
    OWNERSHIP = "missing_ownership"
    STATE = "missing_state"
    CONFLICT = "state_conflict"
    UNKNOWN = "unknown_state"
    MUTATION = "intervening_mutation"
    COVERAGE = "unrepresented_evidence"


class AuditFailure(Exception):
    """Only fixed codes cross the error/log boundary, never exception messages."""

    def __init__(self, kind: FailureType, stage: Stage | None = None,
                 counts: Mapping[str, int] | None = None, reason: FailureReason | None = None):
        self.kind = kind
        self.stage = stage
        self.counts = dict(counts or {})
        self.reason = reason
        super().__init__(kind.value)


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)


def normalized(value: str) -> str:
    # No provider-specific email dot/plus rewriting and no name-based fuzzy joins.
    return unicodedata.normalize("NFC", value.strip()).casefold()


@dataclass(frozen=True)
class RunConfig:
    dataset: Path
    output: Path
    expected_cases: int = 518
    max_artifacts: int = 1000
    max_file_bytes: int = 16 * 1024 * 1024
    max_total_bytes: int = 128 * 1024 * 1024
    max_observations: int = 250_000
    requests_file: str = "deletion_requests.csv"


@dataclass(frozen=True)
class Request:
    case_id: str
    email: str = field(repr=False)
    requested_at: datetime
    reported_status: str
    reported_at: datetime
    audit_at: datetime
    request_text: str = field(repr=False)


@dataclass(frozen=True)
class Identity:
    user_id: str
    identifiers: tuple[Identifier, ...] = field(repr=False)
    updated_at: datetime


@dataclass(frozen=True)
class Change:
    audit_id: str
    user_id: str
    event_time: datetime
    field_name: str
    old_value: str = field(repr=False)
    new_value: str = field(repr=False)


@dataclass(frozen=True)
class Activity:
    activity_id: str
    event_time: datetime
    event_type: str
    source_system: str
    target_system: str
    resource_id: str
    reported_result: str
    details: str = field(repr=False)


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    condition: str
    action: str


@dataclass(frozen=True)
class Artifact:
    file_id: str
    suffix: str
    captured_at: datetime
    content: bytes = field(repr=False)
    sha256: str


@dataclass(frozen=True)
class LoadInput:
    config: RunConfig


@dataclass(frozen=True)
class LoadedInputs:
    requests: tuple[Request, ...]
    identities: tuple[Identity, ...]
    changes: tuple[Change, ...]
    activities: tuple[Activity, ...]
    rules: tuple[Rule, ...]
    artifacts: tuple[Artifact, ...]


@dataclass(frozen=True)
class ExtractionInput:
    inputs: LoadedInputs
    max_observations: int


@dataclass(frozen=True)
class ExtractedEvidence:
    observations: tuple[Observation, ...]
    processed_ids: frozenset[str]
    external_calls: int = 0
    ownership_links: tuple[OwnershipLink, ...] = ()
    inference_candidates: tuple[InferenceCandidate, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    gaps: tuple[EvidenceGap, ...] = ()


@dataclass(frozen=True)
class ArtifactExtraction:
    """Provider must explicitly attest full artifact coverage, even for zero facts."""
    artifact_id: str
    artifact_sha256: str
    observations: tuple[Observation, ...]
    complete: bool
    ownership_links: tuple[OwnershipLink, ...] = ()
    inference_candidates: tuple[InferenceCandidate, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    gaps: tuple[EvidenceGap, ...] = ()


@dataclass(frozen=True)
class IndexInput:
    inputs: LoadedInputs
    evidence: ExtractedEvidence


@dataclass(frozen=True)
class EvidenceIndex:
    observations: tuple[Observation, ...]
    ownership_links: tuple[OwnershipLink, ...]
    by_identifier: Mapping[tuple, tuple[int, ...]]
    by_resource: Mapping[tuple[str, str], tuple[int, ...]]
    by_source: Mapping[str, tuple[int, ...]]
    available_by_source: Mapping[str, datetime]
    available_by_locator: Mapping[tuple[str, str], datetime]
    inference_candidates: tuple[InferenceCandidate, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    gaps: tuple[EvidenceGap, ...] = ()


@dataclass(frozen=True)
class InvestigationInput:
    request: Request
    inputs: LoadedInputs
    index: EvidenceIndex


@dataclass(frozen=True)
class Investigation:
    request: Request
    authorized: bool
    resources: tuple[Observation, ...]
    rules: tuple[Rule, ...]
    ownership_links: tuple[OwnershipLink, ...] = ()
    identity_links: tuple[IdentityLink, ...] = ()
    inference_candidates: tuple[InferenceCandidate, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    intent_assessment: IntentAssessment | None = None


@dataclass(frozen=True)
class IntentAssessment:
    source_id: str
    message_sha256: str
    prompt_version: str
    action: str
    affirmed: bool
    negated: bool
    conditional: bool
    spans: tuple[tuple[int, int, str], ...] = field(repr=False)
    model_provenance: ModelProvenance | None = None


@dataclass(frozen=True)
class CompilationInput:
    investigation: Investigation


@dataclass(frozen=True)
class Step:
    step_no: int
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str


@dataclass(frozen=True)
class CasePlan:
    case_id: str
    deletion_status: str
    steps: tuple[Step, ...]


@dataclass(frozen=True)
class ValidationInput:
    inputs: LoadedInputs
    index: EvidenceIndex
    investigations: tuple[Investigation, ...]
    plans: tuple[CasePlan, ...]


@dataclass(frozen=True)
class ValidatedOutput:
    content: bytes = field(repr=False)
    rows: int
    sha256: str


@dataclass(frozen=True)
class PublicationInput:
    config: RunConfig
    validated: ValidatedOutput


@dataclass(frozen=True)
class Publication:
    rows: int
    bytes_written: int
    sha256: str


I = TypeVar("I")
O = TypeVar("O")


@dataclass(frozen=True)
class ToolContract(Generic[I, O]):
    stage: Stage
    input_type: type[I]
    output_type: type[O]
    permitted_effects: frozenset[Effect] = frozenset()


class Tool(Protocol[I, O]):
    contract: ToolContract[I, O]

    def __call__(self, value: I) -> O: ...


class OptionalExtractor(Protocol):
    """Trusted plugin: receives one in-memory artifact, never the dataset path."""

    def extract(self, artifact: Artifact) -> ArtifactExtraction: ...


LOAD = ToolContract(Stage.LOAD, LoadInput, LoadedInputs, frozenset({Effect.READ_DATASET}))
EXTRACT = ToolContract(Stage.EXTRACT, ExtractionInput, ExtractedEvidence,
                       frozenset({Effect.EXTERNAL_EXTRACTION, Effect.READ_CACHE, Effect.WRITE_CACHE, Effect.WRITE_TEMP}))
INDEX = ToolContract(Stage.INDEX, IndexInput, EvidenceIndex)
INVESTIGATE = ToolContract(Stage.INVESTIGATE, InvestigationInput, Investigation,
                          frozenset({Effect.EXTERNAL_EXTRACTION, Effect.READ_CACHE, Effect.WRITE_CACHE}))
COMPILE = ToolContract(Stage.COMPILE, CompilationInput, CasePlan)
VALIDATE = ToolContract(Stage.VALIDATE, ValidationInput, ValidatedOutput)
PUBLISH = ToolContract(Stage.PUBLISH, PublicationInput, Publication,
                       frozenset({Effect.WRITE_OUTPUT}))
