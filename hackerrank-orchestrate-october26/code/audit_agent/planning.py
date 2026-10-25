"""Policy obligations and exact challenge vocabulary; no model-written plans."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace

from .contracts import (COMPILE, AuditFailure, CasePlan, CompilationInput, FailureType,
                        Investigation, Observation, State, Step)

OPERATIONS = {
    "FINDING": {"REPORT_REMAINING_RECORD": "PRESENT", "REPORT_EXPOSED_PII": "PRESENT",
                "REPORT_ACTIVE_DATA_FLOW": "ACTIVE", "REPORT_RESTORE_RISK": "ACTIVE"},
    "REMEDIATION": {"DISABLE_DATA_FLOW": "DISABLED", "BLOCK_RESTORE": "BLOCKED",
                    "DELETE_RECORD": "ABSENT", "REDACT_RECORD": "REDACTED", "ANONYMIZE_RECORD": "ANONYMIZED"},
    "VERIFICATION": {"VERIFY_RECORD_ABSENT": "ABSENT", "VERIFY_RECORD_PRESENT": "PRESENT",
                     "VERIFY_RECORD_REDACTED": "REDACTED", "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED",
                     "VERIFY_DATA_FLOW_DISABLED": "DISABLED", "VERIFY_RESTORE_BLOCKED": "BLOCKED"},
}
# Reviewed interpretation of supplied prose, not case labels or family shortcuts.
POLICY = {
    "USER_PROFILE": ("DELETE", "Always", None),
    "SECONDARY_IDENTIFIER": ("DELETE", "Always", None),
    "SEARCH_INDEX_ENTRY": ("DELETE", "Always", None),
    "CACHE_ENTRY": ("DELETE", "Always", None),
    "SUPPORT_MESSAGE": ("REDACT", "Conversation contains shared customer, agent, or order context that must be retained", "shared_context"),
    "SUPPORT_ATTACHMENT": ("DELETE", "Attachment belongs only to the deletion subject", "subject_only"),
    "ANALYTICS_PROFILE": ("ANONYMIZE", "Record is still attributable to a user", None),
    "PRODUCT_TELEMETRY": ("ANONYMIZE", "Record is still attributable to a user", None),
    "USER_EXPORT": ("DELETE", "Always", None),
    "MARKETING_PROFILE": ("DELETE", "Always", None),
    "EMAIL_DELIVERY_LOG": ("REDACT", "Log contains a user email address", None),
    "SECURITY_AUDIT_LOG": ("RETAIN", "Record is within the supplied retention period", None),
    "LEGAL_HOLD_RECORD": ("RETAIN", "A supplied legal hold is active", "active_hold"),
    "BACKUP_ARCHIVE": ("RETAIN", "Restore access can be blocked", "restore_blockable"),
    "ACCOUNT_TOMBSTONE": ("REDACT", "Account is deleted and only a stable internal user_id is needed to preserve references to retained records", "tombstone_reference_required"),
}
TREATMENTS = {
    "DELETE": (State.ABSENT, "REPORT_REMAINING_RECORD", "DELETE_RECORD", "VERIFY_RECORD_ABSENT"),
    "REDACT": (State.REDACTED, "REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED"),
    "ANONYMIZE": (State.ANONYMIZED, "REPORT_EXPOSED_PII", "ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED"),
    "RETAIN": (State.PRESENT, None, None, "VERIFY_RECORD_PRESENT"),
    "FLOW": (State.DISABLED, "REPORT_ACTIVE_DATA_FLOW", "DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED"),
    "RESTORE": (State.BLOCKED, "REPORT_RESTORE_RISK", "BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED"),
}


def step_order(step: Step):
    return (tuple(OPERATIONS).index(step.phase), tuple(OPERATIONS[step.phase]).index(step.operation),
            step.system_id, step.resource_id)


@dataclass(frozen=True)
class Obligation:
    key: tuple[str, str]
    desired: State
    finding: str | None
    remediation: str | None
    verification: str
    violated: bool
    witness: Observation
    copies: tuple[Observation, ...]


def obligations(investigation: Investigation) -> tuple[Obligation, ...]:
    rules = defaultdict(list)
    for rule in investigation.rules:
        rules[rule.category].append(rule)
    groups = defaultdict(list)
    for fact in investigation.resources:
        groups[fact.key].append(fact)
    result = []
    for key, copies in sorted(groups.items()):
        categories = {f.category for f in copies}
        if len(categories) != 1:
            raise AuditFailure(FailureType.POLICY)
        category = copies[0].category
        if category == "DATA_FLOW":
            treatment = "FLOW"
        else:
            if category not in POLICY or len(rules[category]) != 1:
                raise AuditFailure(FailureType.POLICY)
            action, condition, witness_key = POLICY[category]
            rule = rules[category][0]
            if (rule.action != action or rule.condition != condition or
                    any(witness_key and witness_key not in f.conditions for f in copies)):
                raise AuditFailure(FailureType.POLICY)
            if category == "SECURITY_AUDIT_LOG" and any(
                    f.retention_until is None or f.retention_until < investigation.request.audit_at
                    for f in copies):
                raise AuditFailure(FailureType.POLICY)
            treatment = "RESTORE" if category == "BACKUP_ARCHIVE" else action
        desired, finding, remediation, verification = TREATMENTS[treatment]
        violating = [f for f in copies if f.state != desired]
        allowed_bad = ({State.PRESENT, State.IDENTIFIABLE, State.REDACTED, State.ANONYMIZED}
                       if treatment == "DELETE" else {State.PRESENT, State.IDENTIFIABLE}
                       if treatment in {"REDACT", "ANONYMIZE"} else {State.ACTIVE})
        if any(f.state not in allowed_bad for f in violating):
            # Includes missing retained data: there is no allowed recreation op.
            raise AuditFailure(FailureType.POLICY)
        if not violating and len({f.evidence_id for f in copies}) > 1:
            # One citation must prove all copies. A richer witness aggregator can
            # be injected later; silently citing one of several copies is unsafe.
            raise AuditFailure(FailureType.UNRESOLVED)
        witnesses = violating or copies
        witness = min(witnesses, key=lambda f: (-f.observed_at.timestamp(), f.evidence_id, f.locator))
        result.append(Obligation(key, desired, finding, remediation, verification,
                                 bool(violating), witness, tuple(copies)))
    return tuple(result)


class CompilePlan:
    contract = COMPILE

    def __call__(self, value: CompilationInput) -> CasePlan:
        investigation = value.investigation
        if not investigation.authorized:
            return CasePlan(investigation.request.case_id, "NOT_APPLICABLE", ())
        required = obligations(investigation)
        if not required:
            raise AuditFailure(FailureType.UNRESOLVED)
        incomplete = any(o.violated for o in required)
        steps = []
        for obligation in required:
            system, resource = obligation.key
            def add(phase, operation, evidence=""):
                if operation is None:
                    raise AuditFailure(FailureType.POLICY)
                steps.append(Step(0, phase, system, resource, operation,
                                  OPERATIONS[phase][operation], evidence))
            if obligation.violated:
                add("FINDING", obligation.finding, obligation.witness.evidence_id)
                add("REMEDIATION", obligation.remediation)
            add("VERIFICATION", obligation.verification,
                "" if incomplete else obligation.witness.evidence_id)
        steps.sort(key=step_order)
        positions = {(s.system_id, s.resource_id): n for n, s in enumerate(steps) if s.phase == "REMEDIATION"}
        for fact in investigation.resources:
            for downstream in fact.downstream:
                if downstream in positions and fact.key in positions:
                    safety_control = fact.category in {"DATA_FLOW", "BACKUP_ARCHIVE"}
                    if (positions[fact.key] < positions[downstream]) != safety_control:
                        raise AuditFailure(FailureType.DEPENDENCY)
        return CasePlan(investigation.request.case_id, "INCOMPLETE" if incomplete else "COMPLETE",
                        tuple(replace(step, step_no=n) for n, step in enumerate(steps, 1)))
