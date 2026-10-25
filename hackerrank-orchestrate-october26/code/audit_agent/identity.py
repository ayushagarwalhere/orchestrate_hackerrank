"""One normalization/resolution path for current and historical identifiers."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .contracts import AuditFailure, FailureReason, FailureType, LoadedInputs, Request
from .evidence import (Assumption, AssumptionCode, Identifier, IdentifierKind, IdentityLink)


@dataclass(frozen=True)
class ResolvedIdentity:
    user_id: str
    keys: frozenset[tuple[IdentifierKind, str]]
    links: tuple[IdentityLink, ...]
    assumptions: tuple[Assumption, ...]


def resolve_identity(request: Request, inputs: LoadedInputs) -> ResolvedIdentity:
    by_user = defaultdict(list)
    assumptions = []
    for identity in inputs.identities:
        if identity.updated_at <= request.audit_at:
            identifiers = (*identity.identifiers, Identifier(IdentifierKind.USER_ID, identity.user_id))
            for identifier in identifiers:
                by_user[identity.user_id].append(IdentityLink(identity.user_id, identifier,
                    "user_identities.csv", identity.user_id, identity.updated_at, "current"))
            assumptions.append(Assumption(AssumptionCode.SNAPSHOT_UPDATE_AVAILABILITY,
                                           "user_identities.csv", identity.user_id))
    for change in inputs.changes:
        if change.event_time <= request.audit_at and change.field_name in {"name", "email", "phone", "email_hash"}:
            kind = IdentifierKind(change.field_name)
            for role, raw in (("historical_old", change.old_value), ("historical_new", change.new_value)):
                if raw:
                    by_user[change.user_id].append(IdentityLink(change.user_id, Identifier(kind, raw),
                        change.audit_id, change.field_name, change.event_time, role))
            by_user[change.user_id].append(IdentityLink(change.user_id,
                Identifier(IdentifierKind.USER_ID, change.user_id), change.audit_id, "user_id",
                change.event_time, "stable_reference"))
            assumptions.append(Assumption(AssumptionCode.CSV_EVENT_AVAILABILITY,
                                           change.audit_id, change.field_name))
    keys = {user: {link.identifier.key for link in links
                   if link.identifier.kind not in {IdentifierKind.NAME, IdentifierKind.UNKNOWN}}
            for user, links in by_user.items()}
    request_key = Identifier(IdentifierKind.EMAIL, request.email).key
    users = [user for user, aliases in keys.items() if request_key in aliases]
    if len(users) != 1:
        raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.IDENTITY)
    user = users[0]
    if any(keys[user] & aliases for other, aliases in keys.items() if other != user):
        raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.IDENTITY)
    links = tuple(by_user[user])
    supports = {(link.source_id, link.locator) for link in links}
    return ResolvedIdentity(user, frozenset(keys[user]), links,
                            tuple(a for a in assumptions if (a.source_id, a.locator) in supports))
