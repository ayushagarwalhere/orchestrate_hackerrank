"""Evidence model shared by every source loader (plan/phases/phase4.md §2.1–§2.3).

An Observation is one grounded statement about one resource at one time, taken from one evidence item.
A Coverage records which resources an authoritative snapshot contained, so a resource missing from it
can be observed as ABSENT by omission.
"""

import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from identity import extract_emails, is_sha256, norm_phone

USER_RE = re.compile(r"\buser_\d+\b")
RESOURCE_RE = re.compile(
    r"\b(?:account|search|support|analytics|export|data_flow|backup|audit_record|legal_hold|tombstone|"
    r"marketing|object|cache|email_delivery)_\d+\b"
)


class State(str, Enum):
    UNKNOWN = "UNKNOWN"
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    IDENTIFIABLE = "IDENTIFIABLE"
    ANONYMIZED = "ANONYMIZED"
    REDACTED = "REDACTED"
    FLOW_ACTIVE = "FLOW_ACTIVE"
    FLOW_DISABLED = "FLOW_DISABLED"
    RESTORE_ALLOWED = "RESTORE_ALLOWED"
    RESTORE_BLOCKED = "RESTORE_BLOCKED"


class Category(str, Enum):
    USER_PROFILE = "USER_PROFILE"
    SEARCH_INDEX_ENTRY = "SEARCH_INDEX_ENTRY"
    ANALYTICS_PROFILE = "ANALYTICS_PROFILE"
    CONTACT_RECORD = "CONTACT_RECORD"  # analytics record keyed only by an identifier (sample case_12) -> DELETE
    SUPPORT_MESSAGE = "SUPPORT_MESSAGE"
    SUPPORT_ATTACHMENT = "SUPPORT_ATTACHMENT"
    USER_EXPORT = "USER_EXPORT"
    MARKETING_PROFILE = "MARKETING_PROFILE"
    DATA_FLOW = "DATA_FLOW"
    BACKUP_ARCHIVE = "BACKUP_ARCHIVE"
    SECURITY_AUDIT_LOG = "SECURITY_AUDIT_LOG"
    LEGAL_HOLD_RECORD = "LEGAL_HOLD_RECORD"
    ACCOUNT_TOMBSTONE = "ACCOUNT_TOMBSTONE"


class Directness(str, Enum):
    DIRECT = "DIRECT"      # the evidence names the resource
    OMISSION = "OMISSION"  # the resource is missing from an authoritative snapshot


# The system_id emitted for each resource prefix. Replica tables report under account_service (sample C12).
SYSTEM_BY_PREFIX = {
    "account": "account_service",
    "search": "search_service",
    "support": "support_platform",
    "analytics": "analytics_platform",
    "export": "export_service",
    "data_flow": "integration_service",
    "backup": "backup_service",
    "audit_record": "security_service",
    "legal_hold": "legal_service",
    "tombstone": "identity_service",
    "marketing": "marketing_platform",
    "object": "object_storage",
}


def resource_prefix(resource_id):
    return re.sub(r"_\d+$", "", resource_id or "")


def system_for(resource_id):
    return SYSTEM_BY_PREFIX.get(resource_prefix(resource_id))


@dataclass(frozen=True)
class Observation:
    evidence_id: str
    file_captured_at: datetime
    observed_at: datetime
    system_id: str
    resource_id: str
    category: Category | None
    state: State
    link_keys: frozenset = frozenset()
    refs: frozenset = frozenset()
    directness: Directness = Directness.DIRECT
    source: str = ""
    identifying_fields: tuple = ()
    source_location: str = ""
    physical_scope: tuple[str, ...] = ()
    observation_time_basis: str = "source"

    @property
    def source_id(self):
        return self.evidence_id

    @property
    def capture_time(self):
        return self.file_captured_at

    def usable(self, audit_at):
        """Two-clock rule: both the file capture time and the record time must be at or before audit_at."""
        return self.observed_at <= self.file_captured_at <= audit_at


@dataclass(frozen=True)
class Coverage:
    """An authoritative snapshot of one system: every resource it held at observed_at is in resource_ids."""
    evidence_id: str
    file_captured_at: datetime
    observed_at: datetime
    system_id: str
    resource_ids: frozenset = field(default_factory=frozenset)
    kind: str = ""  # "topology_table" | "empty_snapshot"
    source: str = ""
    covered_scopes: tuple[str, ...] = ()
    category: Category = Category.USER_PROFILE

    def usable(self, audit_at):
        return self.file_captured_at <= audit_at and self.observed_at <= audit_at

    def proves_absent(self, resource_id):
        return (self.kind in {"topology_table", "empty_snapshot"} and
                self.category is Category.USER_PROFILE and resource_prefix(resource_id) == "account" and
                system_for(resource_id) == self.system_id and resource_id not in self.resource_ids)


class Presence(str, Enum):
    MISSING = "MISSING"
    NULL = "NULL"
    VALUE = "VALUE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class IdentifyingField:
    path: str
    presence: Presence
    value_json: str | None = field(default=None, repr=False)


IDENTIFYING = frozenset({"name", "full_name", "display_name", "user_id", "customer_reference", "subject_reference",
    "email", "phone", "email_hash", "owner_email", "owner_phone", "requester_email", "requester_name", "requester_phone"})


def identifying_fields(record):
    """Raw identifying fields, not lookup selectors inferred from a query."""
    fields = []
    def walk(value, path=""):
        if isinstance(value, dict):
            for key, item in value.items():
                child = path + "/" + str(key)
                if key in IDENTIFYING:
                    fields.append(IdentifyingField(child, Presence.NULL if item is None else Presence.VALUE,
                        None if item is None else json.dumps(item, ensure_ascii=False, sort_keys=True)))
                walk(item, child)
        elif isinstance(value, list):
            for n, item in enumerate(value): walk(item, path + "/" + str(n))
    walk(record)
    present = {item.path.rsplit("/", 1)[-1] for item in fields}
    fields.extend(IdentifyingField("/" + key, Presence.MISSING) for key in sorted(IDENTIFYING - present))
    return tuple(fields)


def text_identifying_fields(text):
    values = {"email": sorted(extract_emails(text)), "user_id": sorted(set(USER_RE.findall(text))),
              "phone": sorted(set(re.findall(r"(?<!\w)\+\d[\d ().-]{6,}\d", text)))}
    fields = [IdentifyingField(f"/{key}/{n}", Presence.VALUE, json.dumps(value, ensure_ascii=False))
              for key, items in values.items() for n, value in enumerate(items)]
    # Retain text for reviewed extraction of names/other identifiers. No claim
    # that unparsed names or local-format phones were absent from the source.
    fields.extend(IdentifyingField("/" + key, Presence.UNKNOWN) for key in ("name", "email_hash"))
    fields.append(IdentifyingField("/uninterpreted_text", Presence.VALUE, json.dumps(text, ensure_ascii=False)))
    return tuple(fields)


def _strings(value, key=""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _strings(v, k)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for v in value:
            yield from _strings(v, key)
    elif isinstance(value, str):
        yield key, value


def link_keys_from(*values):
    """Exact identifier keys found anywhere in nested record values (emails in free text included)."""
    keys = set()
    for value in values:
        for key, text in _strings(value):
            keys |= {("email", e) for e in extract_emails(text)}
            keys |= {("user", u) for u in USER_RE.findall(text)}
            if is_sha256(text):
                keys.add(("hash", text.strip().lower()))
            if "phone" in key.lower() and norm_phone(text):
                keys.add(("phone", norm_phone(text)))
    return frozenset(keys)


def resource_refs_from(*values, exclude=None):
    """Other resource ids mentioned in record values (e.g. source_resource_id, repopulated targets)."""
    refs = set()
    for value in values:
        for _, text in _strings(value):
            refs |= set(RESOURCE_RE.findall(text))
    refs.discard(exclude)
    return frozenset(refs)
