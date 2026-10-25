"""Evidence vocabulary: readings, subject links, and deductions are distinct."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import unicodedata


class State(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    IDENTIFIABLE = "IDENTIFIABLE"
    REDACTED = "REDACTED"
    ANONYMIZED = "ANONYMIZED"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class IdentifierKind(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    EMAIL_HASH = "email_hash"
    USER_ID = "user_id"
    NAME = "name"
    UNKNOWN = "unknown"


def canonical_identifier(kind: IdentifierKind, raw: str) -> str:
    text = unicodedata.normalize("NFC", raw.strip())
    if kind is IdentifierKind.PHONE:
        # Remove formatting only. Never drop +, country digits, trunk zeroes,
        # or match by suffix. Local and international numbers remain distinct.
        return re.sub(r"[\s().-]", "", text)
    return text.casefold()


@dataclass(frozen=True)
class Identifier:
    kind: IdentifierKind
    raw: str = field(repr=False)

    @property
    def key(self) -> tuple[IdentifierKind, str]:
        return self.kind, canonical_identifier(self.kind, self.raw)


def reference_identifier(raw: str) -> Identifier:
    text = raw.strip()
    if "@" in text:
        kind = IdentifierKind.EMAIL
    elif re.fullmatch(r"user_[\w]+", text, re.IGNORECASE):
        kind = IdentifierKind.USER_ID
    elif re.fullmatch(r"[a-fA-F0-9]{64}", text):
        kind = IdentifierKind.EMAIL_HASH
    elif re.fullmatch(r"\+?[0-9][0-9\s().-]+", text):
        kind = IdentifierKind.PHONE
    else:
        kind = IdentifierKind.UNKNOWN
    return Identifier(kind, raw)


class ScopeKind(str, Enum):
    RESOURCE_LOOKUP = "resource_lookup"
    DATABASE_QUERY = "database_query"


@dataclass(frozen=True)
class EvidenceScope:
    kind: ScopeKind = ScopeKind.RESOURCE_LOOKUP
    table: str | None = None
    covered_tables: tuple[str, ...] = ()

    @property
    def partition(self) -> tuple[ScopeKind, str | None]:
        return self.kind, self.table


class FieldPresence(str, Enum):
    MISSING = "missing"
    NULL = "null"
    VALUE = "value"


@dataclass(frozen=True)
class FieldFact:
    name: str
    presence: FieldPresence
    value: str | None = field(default=None, repr=False)


class Permission(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PermissionFact:
    name: str
    value: Permission = Permission.UNKNOWN


@dataclass(frozen=True)
class ModelProvenance:
    source_id: str
    content_sha256: str
    captured_at: datetime
    prompt_version: str
    prompt_sha256: str
    schema_version: str
    response_sha256: str
    schema_sha256: str


@dataclass(frozen=True)
class Observation:
    evidence_id: str
    locator: str
    system_id: str
    resource_id: str
    category: str
    state: State
    captured_at: datetime
    observed_at: datetime
    available_at: datetime
    copy_id: str = "logical"
    conditions: tuple[str, ...] = ()
    retention_until: datetime | None = None
    downstream: tuple[tuple[str, str], ...] = ()
    scope: EvidenceScope = EvidenceScope()
    fields: tuple[FieldFact, ...] = ()
    permissions: tuple[PermissionFact, ...] = ()
    model_provenance: ModelProvenance | None = None

    @property
    def source_id(self) -> str:
        return self.evidence_id

    @property
    def key(self) -> tuple[str, str]:
        return self.system_id, self.resource_id

    @property
    def physical_key(self) -> tuple:
        return self.system_id, self.resource_id, self.copy_id, self.scope.partition


class OwnershipBasis(str, Enum):
    SUBJECT_REFERENCE = "subject_reference"
    CATALOG_REFERENCE = "catalog_reference"


@dataclass(frozen=True)
class OwnershipLink:
    source_id: str
    locator: str
    system_id: str
    resource_id: str
    identifier: Identifier = field(repr=False)
    captured_at: datetime
    observed_at: datetime
    available_at: datetime
    basis: OwnershipBasis = OwnershipBasis.SUBJECT_REFERENCE
    model_provenance: ModelProvenance | None = None

    @property
    def key(self) -> tuple[str, str]:
        return self.system_id, self.resource_id


@dataclass(frozen=True)
class IdentityLink:
    user_id: str
    identifier: Identifier = field(repr=False)
    source_id: str
    locator: str
    available_at: datetime
    role: str


class AssumptionCode(str, Enum):
    CSV_EVENT_AVAILABILITY = "csv_event_availability"
    SNAPSHOT_UPDATE_AVAILABILITY = "snapshot_update_availability"
    REFERENCE_NAMING = "reference_naming"
    LOGICAL_COPY_SCOPE = "logical_copy_scope"
    SUMMARY_READBACK = "summary_readback"
    CARRY_FORWARD = "state_carry_forward"
    RETROSPECTIVE_LINK = "retrospective_resource_link"
    RESOURCE_COVERAGE = "resource_lookup_coverage"
    SCREENSHOT_CAPTURE_TIME = "screenshot_capture_observation_time"
    SCREENSHOT_TRANSCRIPTION = "model_screenshot_transcription"


@dataclass(frozen=True)
class Assumption:
    code: AssumptionCode
    source_id: str
    locator: str
    resource_key: tuple[str, str] | None = None


class InferenceKind(str, Enum):
    CARRY_FORWARD = "carry_forward"
    RETROSPECTIVE_LINK = "retrospective_link"
    DOWNSTREAM_ASSOCIATION = "downstream_association"
    UNCLASSIFIED_REFERENCE = "unclassified_reference"


@dataclass(frozen=True)
class InferenceCandidate:
    kind: InferenceKind
    resource_key: tuple[str, str]
    support: tuple[tuple[str, str], ...]
    proposed_state: State | None = None
    assumptions: tuple[AssumptionCode, ...] = ()


@dataclass(frozen=True)
class EvidenceBundle:
    observations: tuple[Observation, ...] = ()
    ownership_links: tuple[OwnershipLink, ...] = ()
    inference_candidates: tuple[InferenceCandidate, ...] = ()
    assumptions: tuple[Assumption, ...] = ()
    gaps: tuple[EvidenceGap, ...] = ()


@dataclass(frozen=True)
class EvidenceGap:
    """Subject text was read but cannot be assigned a grounded resource/state."""
    source_id: str
    locator: str
    captured_at: datetime
    identifiers: tuple[Identifier, ...] = field(repr=False)
