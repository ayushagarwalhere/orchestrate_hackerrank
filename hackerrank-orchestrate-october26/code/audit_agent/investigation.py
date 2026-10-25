"""One reusable index; per-request temporal joins and conservative reconstruction."""
from __future__ import annotations

from collections import defaultdict, deque
from types import MappingProxyType
import re

from .contracts import (INDEX, INVESTIGATE, AuditFailure, EvidenceIndex, FailureReason, FailureType, IndexInput,
                        Investigation, InvestigationInput, Observation, normalized)
from .evidence import (Assumption, AssumptionCode, EvidenceBundle, InferenceCandidate, InferenceKind,
                       OwnershipBasis, OwnershipLink, State, reference_identifier)
from .extraction import validate_bundle
from .identity import resolve_identity


class IndexEvidence:
    contract = INDEX

    def __call__(self, value: IndexInput) -> EvidenceIndex:
        evidence = value.evidence
        artifacts = {a.file_id: a for a in value.inputs.artifacts}
        if evidence.processed_ids != frozenset(artifacts):
            raise AuditFailure(FailureType.INDEX)
        by_identifier = defaultdict(list)
        by_resource = defaultdict(list)
        by_source = defaultdict(list)
        for source, artifact in artifacts.items():
            bundle = EvidenceBundle(tuple(f for f in evidence.observations if f.source_id == source),
                tuple(link for link in evidence.ownership_links if link.source_id == source),
                tuple(c for c in evidence.inference_candidates if c.support and c.support[0][0] == source),
                tuple(a for a in evidence.assumptions if a.source_id == source),
                tuple(g for g in evidence.gaps if g.source_id == source))
            validate_bundle(artifact, bundle)
        if (any(link.source_id not in artifacts for link in evidence.ownership_links) or
                any(a.source_id not in artifacts for a in evidence.assumptions) or
                any(g.source_id not in artifacts for g in evidence.gaps) or
                any(not c.support or c.support[0][0] not in artifacts for c in evidence.inference_candidates)):
            raise AuditFailure(FailureType.INDEX)
        for n, fact in enumerate(evidence.observations):
            if fact.evidence_id not in artifacts:
                raise AuditFailure(FailureType.INDEX)
            by_resource[fact.key].append(n)
            by_source[fact.evidence_id].append(n)
        links = list(evidence.ownership_links)
        assumptions = list(evidence.assumptions)
        for activity in value.inputs.activities:
            if activity.event_type != "LINK_RESOURCE_IDENTITY":
                continue
            for token in sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]+|user_[A-Za-z0-9_]+", activity.details))):
                links.append(OwnershipLink(activity.activity_id, "details", activity.target_system,
                    activity.resource_id, reference_identifier(token), activity.event_time,
                    activity.event_time, activity.event_time, OwnershipBasis.CATALOG_REFERENCE))
            assumptions.append(Assumption(AssumptionCode.CSV_EVENT_AVAILABILITY,
                                           activity.activity_id, "details", (activity.target_system, activity.resource_id)))
            assumptions.append(Assumption(AssumptionCode.REFERENCE_NAMING,
                                           activity.activity_id, "details", (activity.target_system, activity.resource_id)))
        for n, link in enumerate(links):
            by_identifier[link.identifier.key].append(n)
        source_times = {source: artifact.captured_at for source, artifact in artifacts.items()}
        source_times.update({a.activity_id: a.event_time for a in value.inputs.activities})
        locator_times = {}
        for item in (*evidence.observations, *links):
            at = max(item.captured_at, item.observed_at, item.available_at)
            source_times[item.source_id] = max(source_times[item.source_id], at)
            ref = (item.source_id, item.locator)
            locator_times[ref] = max(locator_times.get(ref, at), at)
        freeze = lambda mapping: MappingProxyType({k: tuple(v) for k, v in mapping.items()})
        return EvidenceIndex(evidence.observations, tuple(links), freeze(by_identifier), freeze(by_resource),
                             freeze(by_source), MappingProxyType(source_times), MappingProxyType(locator_times),
                             evidence.inference_candidates, tuple(assumptions), evidence.gaps)


def request_authorizes(text: str) -> bool:
    """Recognize explicit deletion or review of an earlier deletion, not consent
    inferred from a reported workflow status. This authorizes an offline audit;
    the coordinator has no effect that executes account deletion.
    """
    text = normalized(text).replace("’", "'")
    if re.match(r"^(?:hi[,! ]+)?(?:how (?:can|do|would)|what (?:is|does)|why (?:is|does))\b", text):
        if not re.search(r"\bplease (?:delete|erase|remove|close|audit|verify)\b", text):
            return False
    restoration = re.search(r"\b(?:please |can you |i want (?:you )?to )?(?:restore|reopen|recover|reactivate) my account\b", text)
    if restoration:
        # A report of accidental prior deletion does not authorize a new
        # deletion. Explicit conflicting new actions still require review.
        if re.search(r"\bplease (?:delete|erase|close)\b", text):
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
        return False
    # UI labels may be quoted in an otherwise explicit request. Quoted
    # destructive instructions are untrusted examples, not authorization.
    for quoted in re.findall(r'"([^"\n]*)"|“([^”\n]*)”|`([^`\n]*)`', text):
        if re.search(r"\b(?:delet\w*|eras\w*|clos\w*|remov\w*)\b", " ".join(quoted)):
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
    text = re.sub(r'"[^"\n]*"|“[^”\n]*”|`[^`\n]*`', ' ', text)
    if any(mark in text for mark in ('"', '“', '”', '`')):
        raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
    # A condition governing permitted retention is distinct from a condition
    # governing deletion. Split only explicit retention clauses, not 'but only
    # if', which must still make deletion unresolved.
    text = re.sub(r"\s+(?:but\s+)?(?:(?:you\s+)?(?:can|may)\s+)?(?:keep(?:ing)?|retain(?:ing)?|preserve)\b",
                  lambda match: "; " + match.group(0).strip(), text)
    clauses = re.split(r"[.!?;。]", text)
    destructive = r"\b(?:delet\w*|eras\w*|clos\w*|remov\w*)\b"
    # Conditions on contacting the requester or policy retention do not make an
    # otherwise explicit account-deletion request conditional. Conditions on
    # deletion itself do. Unsupported scope stays unresolved for intent review.
    for clause in clauses:
        # 'deleted-account reference' is the name of a retained record, not
        # an instruction to delete that record if its retention is required.
        clause = re.sub(r"\bdeleted[- ]account (?:reference|record|tombstone)\b", "stable reference", clause)
        if re.search(destructive, clause) and re.search(r"\b(?:unless|only if|only after|perhaps|maybe)\b", clause):
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
        if re.search(r"\bif\b.{0,100}" + destructive, clause) or re.search(destructive + r".{0,100}\bif\b", clause):
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
    negative = bool(re.search(r"\b(?:do not|don't|not a request to) (?:delete|erase|close) (?:my |this |the )?(?:account|personal data|anything)\b", text))
    negative = negative or bool(re.search(
        r"\bnot a request to (?:delete|erase)\b|\b(?:not asking for|not a request for) deletion\b|\b(?:do not|don't) (?:delete|erase)(?: or change)? (?:it|anything)\b", text))
    full_object = r"(?:account|personal[- ]data|personal information)"
    affirmative = any(
        not re.search(r"\b(?:not|don't|never)\b", clause) and
        re.search(r"\b(?:(?:delete|deleting|erase|remove|close) (?:my|this|the) " + full_object + r"|"
                  + full_object + r".{0,55}(?:deleted|erased|closed)|"
                  r"account[- ]deletion|deletion of (?:my|this|the) account|personal-data deletion)\b", clause)
        for clause in clauses)
    # Direct removal of the subject's profile/identifiers is in scope even
    # when retained shared conversations or stable references may remain.
    affirmative = affirmative or any(
        not re.search(r"\b(?:not|don't|never)\b", clause) and
        re.search(r"\b(?:please\s+)?(?:remove|erase|delete) my (?:profile|personal (?:data|details|information))\b", clause)
        for clause in clauses)
    # Prior-deletion statements plus requests to verify/finish are in scope of
    # the audit even when no new imperative to delete is present.
    prior = bool(re.search(r"\b(?:i (?:deleted|closed) (?:my|this) account|"
                          r"account (?:had been|was|has been) deleted|"
                          r"account (?:page |itself )?is gone|deletion was complete)\b", text))
    review = bool(re.search(r"\b(?:check|verify|audit|confirm|inspect|investigate|finish|remove|delete|erase|handle|keep only)\b", text))
    prior_review = prior and review
    account_context = bool(re.search(r"\b(?:my|this|the) account\b", text))
    prior_review = prior_review or bool(account_context and review and (
        re.search(r"\bbefore deleting it\b|\baccount (?:had been|has been|was) (?:fully )?(?:removed|deleted)\b", text) or
        re.search(r"\b(?:confirm|verify|check|tell me whether)\b.{0,120}\b(?:account|profile)\b.{0,90}\b(?:removed|gone)\b", text)))
    affirmative = affirmative or bool(
        re.search(r"\bplease audit (?:the|my) deletion\b", text) or
        re.search(r"\bplease (?:begin|start|initiate) (?:the |my )?deletion process for (?:my|this|the) account\b", text) or
        account_context and re.search(r"\bplease remove records (?:linked to|under) both\b", text) or
        account_context and re.search(r"\bplease remove my name and contact details\b", text))
    # Narrow multilingual full-account deletion patterns; other languages and
    # partial/negated requests must reach the optional intent adapter.
    multilingual = (bool(re.search(r"\b(?:je demande|veuillez).{0,35}suppression.{0,35}(?:du|de mon) compte\b", text)) or
        bool(re.search(r"\b(?:intenté|quiero|solicito) eliminar mi cuenta\b", text)) or
        bool(re.search(r"\bsolicito.{0,35}eliminación.{0,35}de (?:la|mi) cuenta\b", text)) or
        bool(re.search(r"\b(?:solicito|peço).{0,35}(?:exclusão|eliminação).{0,35}(?:da (?:minha )?|de minha )conta\b", text)) or
        bool(re.search(r"계정.{0,20}삭제.{0,12}(?:요청|부탁)합니다", text)) or
        bool(re.search(r"アカウント.{0,12}削除を(?:依頼|お願い)します", text)))
    if multilingual and re.search(r"\b(?:ne|pas|não|nao)\b|\bno\b.{0,30}\b(?:eliminar|solicito)\b|削除しない|削除しないで|하지\s*(?:않|마)|요청하지|삭제.{0,8}(?:않|말)|계정.{0,25}면", text):
        raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
    if multilingual:
        for clause in clauses:
            if (re.search(r"eliminación|exclusão|eliminação|suppression", clause) and
                    re.search(r"\b(?:si|se|sauf)\b", clause)):
                raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
    affirmative = affirmative or prior_review or multilingual
    if affirmative:
        if negative:
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
        return True
    # Correction and channel preferences can explicitly prohibit removal
    # without using the full phrase 'do not delete my account'.
    if (re.search(r"\b(?:correct|replace)\b", text) and
            re.search(r"\b(?:leave the account active|without (?:removing|deleting))\b", text)):
        return False
    if re.search(r"\b(?:not asking for|not a request for) deletion\b", text):
        return False
    nondeletion = re.search(
        r"\b(?:download|export|copy|information request|reset|marketing|change (?:the|my) email|correct|give me access)\b", text)
    if negative or nondeletion:
        # An unrecognized affirmative destructive phrase is not a safe opt-out.
        if re.search(r"\b(?:delete|erase|deletion|erasure)\b", text) and not negative:
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
        if any(re.search(r"\b(?:delet\w*|eras\w*|clos\w*|forget\w*|remov\w*)\b", clause) and
               not re.search(r"\b(?:do not|don't|not a request to) (?:delete|erase|close)", clause) and
               not re.search(r"remove me from marketing lists only", clause) for clause in clauses):
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)
        return False
    raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.INTENT)


class Investigate:
    contract = INVESTIGATE

    def __init__(self, intent_interpreter=None):
        self.intent_interpreter = intent_interpreter

    def __call__(self, value: InvestigationInput) -> Investigation:
        request, inputs, index = value.request, value.inputs, value.index
        assessment = None
        try:
            authorized = request_authorizes(request.request_text)
        except AuditFailure as error:
            if error.kind is not FailureType.UNRESOLVED or self.intent_interpreter is None:
                raise
            from .model_adapters import validate_intent_assessment
            assessment = self.intent_interpreter.interpret(request)
            authorized = validate_intent_assessment(request, assessment)
        if not authorized:
            return Investigation(request, False, (), inputs.rules, intent_assessment=assessment)
        cutoff = request.audit_at
        identity = resolve_identity(request, inputs)
        if any(g.captured_at <= cutoff and (not g.identifiers or
               any(i.key in identity.keys for i in g.identifiers)) for g in index.gaps):
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.COVERAGE)

        def eligible(fact: Observation) -> bool:
            return fact.observed_at <= cutoff and fact.available_at <= cutoff

        selected = set()
        used_links = []
        for alias in sorted(identity.keys):
            for n in index.by_identifier.get(alias, ()):
                link = index.ownership_links[n]
                if max(link.captured_at, link.observed_at, link.available_at) <= cutoff:
                    selected.add(link.key)
                    used_links.append(link)
        candidates = []
        assumptions = list(identity.assumptions)
        queue = deque(sorted(selected))
        while queue:
            key = queue.popleft()
            facts = [index.observations[n] for n in index.by_resource.get(key, ())
                     if eligible(index.observations[n])]
            if not facts:
                raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.STATE)
            for fact in facts:
                for edge in fact.downstream:
                    if edge not in selected:
                        selected.add(edge)
                        queue.append(edge)
                        candidates.append(InferenceCandidate(InferenceKind.DOWNSTREAM_ASSOCIATION, edge,
                                                              ((fact.source_id, fact.locator),)))

        latest = []
        for key in sorted(selected):
            copies = defaultdict(list)
            for n in index.by_resource[key]:
                fact = index.observations[n]
                if eligible(fact):
                    copies[(fact.copy_id, fact.scope.partition)].append(fact)
            for facts in copies.values():
                newest = max(f.observed_at for f in facts)
                final = [f for f in facts if f.observed_at == newest]
                if len({(f.state, f.category, f.conditions, f.retention_until, f.downstream, f.permissions)
                        for f in final}) != 1:
                    raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.CONFLICT)
                witness = min(final, key=lambda f: (f.evidence_id, f.locator))
                if witness.state is State.UNKNOWN:
                    raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.UNKNOWN)
                # Mutation claims after a readback invalidate its continuity. They
                # are not promoted to proof that a mutation succeeded.
                mutations = {"UPDATE_RECORD", "SYNC_RECORD", "RESTORE_BACKUP", "INDEX_RECORD",
                             "REFRESH_CACHE", "CREATE_EXPORT", "ANONYMIZE_RECORD", "REDACT_RECORD",
                             "DISABLE_DATA_FLOW", "BLOCK_RESTORE"}
                if any(a.resource_id == key[1] and a.target_system == key[0] and
                       newest < a.event_time <= cutoff and a.event_type in mutations
                       for a in inputs.activities):
                    raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.MUTATION)
                latest.append(witness)
                if witness.observed_at < cutoff:
                    candidates.append(InferenceCandidate(InferenceKind.CARRY_FORWARD, key,
                        ((witness.source_id, witness.locator),), witness.state, (AssumptionCode.CARRY_FORWARD,)))
                    assumptions.append(Assumption(AssumptionCode.CARRY_FORWARD, witness.source_id, witness.locator, key))
                for link in used_links:
                    if link.key == key and link.observed_at > witness.observed_at:
                        candidates.append(InferenceCandidate(InferenceKind.RETROSPECTIVE_LINK, key,
                            ((link.source_id, link.locator), (witness.source_id, witness.locator)),
                            assumptions=(AssumptionCode.RETROSPECTIVE_LINK,)))
                        assumptions.append(Assumption(AssumptionCode.RETROSPECTIVE_LINK, link.source_id, link.locator, key))
        if not latest:
            raise AuditFailure(FailureType.UNRESOLVED, reason=FailureReason.OWNERSHIP)
        def support_eligible(ref):
            # Unknown locators use the conservative latest availability for the
            # source. Future metadata must not enter an earlier reasoning trace.
            return index.available_by_locator.get(ref, index.available_by_source[ref[0]]) <= cutoff

        assumptions.extend(a for a in index.assumptions if a.resource_key in selected and
                           support_eligible((a.source_id, a.locator)))
        candidates.extend(c for c in index.inference_candidates if c.resource_key in selected and
                          all(support_eligible(ref) for ref in c.support))
        return Investigation(request, True, tuple(latest), inputs.rules, tuple(used_links), identity.links,
                             tuple(candidates), tuple(dict.fromkeys(assumptions)), assessment)
