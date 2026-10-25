"""Conservative request interpretation with an explicit uncertain result.

Reliable clause-scoped rules distinguish privacy request types. Retention
qualifies treatment rather than negating deletion. Only genuinely ambiguous
messages reach the classification-only v3 prompt; failed or malformed responses
remain UNSURE and cannot publish a NOT_APPLICABLE row.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DELETION = "DELETION"
NOT_APPLICABLE = "NOT_APPLICABLE"
UNSURE = "UNSURE"

# Refusal/scope cues are interpreted per clause; conflicts remain uncertain.
OVERRIDE_CUES = [
    r"\b(?:do not|don't|dont|never) (?:want|wish|consent|authorize|allow|permit|let|proceed).{0,60}\b(?:delete|erase|remove|close)\b",
    r"\bno (?:need|permission|authorization) to (?:delete|erase|remove|close)\b",
    r"\b(?:cancel|withdraw|revoke) (?:my|the|this).{0,50}\b(?:deletion|erasure|delete|erase)\b",
    r"\bnot (?:asking|requesting|looking) (?:for|to) (?:the )?(?:deletion|delete|erasure|erase|removal|remove)",
    r"\bnot a (?:deletion|erasure) request\b",
    r"\bnot a request to (?:erase|delete|remove|close)\b",
    r"\b(?:do not|don't|dont|never) (?:delete|erase|remove|close|deactivate)\b",
    r"\bwithout (?:removing|deleting|erasing|closing)\b",
    r"\b(?:keep|leave) (?:the|my|this) (?:account|profile)(?: \w+)? (?:as it is|active|open|in place)\b",
    r"\bleave (?:the|my) (?:account|profile)\b.*\b(?:active|in place|as it is)\b",
    r"\b(?:i )?(?:want|would like|need) to (?:continue|keep) using\b",
    r"\bi still (?:use|need) (?:it|the account|this account|my account)\b",
    r"\bmarketing (?:lists?|emails?|messages?|communications?) only\b",
    r"\bonly (?:from|the) marketing\b",
    r"\bremove me from (?:the |your |all )?(?:marketing|mailing|newsletter|promotional|email)\b(?!.*\b(?:delete|erase|close)\b)",
    # wants data or an account back rather than gone ("backups must not be able to restore" is not matched)
    r"\b(?:please|can you|could you|i want to|i'd like to|i would like to|help me) (?:restore|recover|reactivate|undo|reinstate|reopen)\b",
    # es / fr / pt / ja / ko refusals
    r"\bno (?:quiero|deseo) (?:eliminar|borrar|cerrar)\b",
    r"\bsin (?:eliminar|borrar)\b",
    r"\bne (?:demande|souhaite|veux) pas (?:la )?(?:suppression|supprimer|fermer)\b",
    r"\bsans supprimer\b",
    r"\bnão (?:quero|desejo|solicito) (?:a )?(?:exclusão|excluir|apagar)\b",
    r"削除しないで|削除は不要|削除を希望しません",
    r"삭제하지 ?마|삭제를 원하지 않",
]

# Boilerplate that mentions deletion procedurally; a deletion cue found only here does not decide intent.
BOILERPLATE = [
    r"deletion policy",
    r"deletion procedure",
    r"retention and deletion requirements",
    r"eligible for deletion",
    r"scope of the deletion request",
    r"standard personal-data deletion",
]


@dataclass(frozen=True)
class IntentResult:
    label: str
    rule: str
    cue: str
    intent: str = "unknown"
    retention_allowed: bool | None = None


class UnresolvedIntentError(ValueError):
    """An unresolved authorization must never become NOT_APPLICABLE."""


def normalize(text):
    text = unicodedata.normalize("NFKC", text).lower()
    return text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?。？！])\s*", text) if s.strip()]


def _first(patterns, text):
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0)
    return None


def classify(text):
    if not isinstance(text, str) or not text.strip():
        return IntentResult(UNSURE, "invalid_or_empty", "")
    try:
        return _classify(text)
    except Exception:
        return IntentResult(UNSURE, "parser_failure", "")


KINDS = {"deletion", "access", "correction", "export", "marketing_opt_out", "restoration", "question", "unknown"}
OBJECT = r"(?:account|profile|personal[- ]data|personal information|personal details|records?|data|identifiers?|traces?|copies|name|contact details)"
EXPLICIT = [
    r"\b(?:delete|erase|remove|wipe|purge|scrub|close)\s+(?:(?:all|any|every|remaining|permanently|completely|of|the|my|this|that|these|associated|linked|old|current)\s+){0,8}" + OBJECT + r"\b",
    r"\b(?:want|like|need|request|requesting|asking).{0,100}\b(?:account|profile|personal[- ]data|personal information).{0,65}\b(?:deleted|erased|closed|removed)\b",
    r"\b(?:request|requesting|asking|begin|process|submit|treat|finish|complete|audit|verify).{0,75}\b(?:deletion|erasure)\b",
    r"\b(?:this|my|the) account\b.{0,70}\b(?:want|like|need) it (?:permanently )?(?:deleted|erased|closed|removed)\b",
    r"\b(?:i am|i'm) deleting (?:my|this|the) account\b|\bright to be forgotten\b|\bforget me\b",
    r"\b(?:solicito|quiero|intenté).{0,30}\b(?:eliminar|eliminación|borrar)\b.{0,60}\b(?:cuenta|datos)\b",
    r"\b(?:je demande|veuillez|je souhaite).{0,40}\b(?:suppression|supprimer|effacer)\b.{0,60}\b(?:compte|données)\b",
    r"\b(?:solicito|quero).{0,30}\b(?:exclusão|excluir|apagar)\b.{0,60}\b(?:conta|dados)\b",
    r"アカウント.{0,30}削除.{0,15}(?:依頼|お願い|ください)|계정.{0,30}삭제.{0,15}(?:요청|주세요)",
]
QUESTION = (r"^(?:(?:please )?(?:tell me|explain|show me|describe)\b|"
    r"(?:can|could) you (?:please )?(?:tell me|explain|show me|describe)\b|"
    r"i (?:want|need|would like) to (?:know|understand)\b|"
    r"how (?:to|do|can|would|does|long)|what (?:happens|is|does|would|will)|"
    r"why (?:is|does|was)|can i|can a |do you|does (?:deleting|deletion|your)|"
    r"if i (?:delete|close)|is it possible)\b")
RETENTION = r"\b(?:retain\w*|retention|keep\w*|preserv\w*|may remain|can stay|may stay|except)\b"
REQUIRED = r"\b(?:law|legal\w*|require\w*|policy|security|anonymous|statistics|backups?|stable|internal|reference|shared|conversation)\b"
NON_KINDS = [
    ("restoration", r"^(?:restore|recover|reactivate|reopen)\b|\b(?:please|can you|could you|i want to|i'd like to|help me).{0,20}\b(?:restore|recover|reactivate|undo|reinstate|reopen)\b"),
    ("marketing_opt_out", r"\b(?:unsubscribe|stop.{0,30}(?:promotional|marketing)|remove (?:me|my email) from.{0,30}(?:marketing|mailing|newsletter)|marketing.{0,20}only)\b"),
    ("export", r"\b(?:copy|download|export|portable|invoices?|receipts?)\b"),
    ("correction", r"\b(?:correct|correction|misspelled|replace|update|change|out of date)\b"),
    ("access", r"\b(?:access|login|log in|password|reset|what (?:personal )?(?:information|data)|(?:store|hold|keep|have) (?:on|about) me)\b"),
]


def _classify(text):
    norm = normalize(text)
    quoted = bool(re.search(r'"[^"\n]*"|`[^`]*`', norm))
    norm = re.sub(r'"[^"\n]*"|`[^`]*`', " ", norm)
    if re.search(r"\b(?:replace (?:it|the|my)|correct (?:it|the spelling)|change (?:it|the spelling))\b", norm) and not re.search(
            r"\b(?:delete|erase|remove|close).{0,30}\b(?:account|profile|personal data|personal information)\b", norm):
        return IntentResult(NOT_APPLICABLE, "explicit_correction", "", "correction")
    clauses = [s.strip() for s in re.split(r"[!?。？！;]|\.(?:\s|$)", norm) if s.strip()]
    yes, no, uncertain, retained = [], [], False, False
    for clause in clauses:
        retention = bool(re.search(RETENTION, clause) and re.search(REQUIRED, clause))
        retention |= bool(re.search(r"(?:do not|don't) (?:delete|erase|remove).{0,25}(?:legally|required|legal|security).{0,25}(?:records|logs|invoices)", clause))
        retained |= retention
        refusal = _first(OVERRIDE_CUES, clause)
        whole_refusal = re.search(r"(?:do not|don't|never|no permission|no authorization).{0,100}\b(?:account|profile|personal data|personal information)\b", clause)
        limited = retention and not whole_refusal
        # Restoration is a distinct request, not consent to delete a previously
        # deleted account. Marketing and continued-use limits are handled below.
        if refusal and not limited and not re.search(NON_KINDS[0][1], clause):
            if _first(EXPLICIT, clause) and re.search(r"^(?:please )?(?:delete|erase|remove|close)\b|\bbut (?:please )?(?:delete|erase|remove|close)\b", clause):
                yes.append("conflicting_request")
            no.append(refusal)
            continue
        if re.search(QUESTION, clause):
            independent = re.search(r"\band (?:please )?(?:delete|erase|remove|close) (?:my|this|the)\b", clause)
            if independent is None:
                continue
            clause = clause[independent.start() + len("and "):]
        # Retention tails and courtesy conditions qualify treatment, rather than
        # making a preceding independent authorization conditional.
        core = re.split(r"[,;]?\s+(?:but )?(?:you (?:may|can)|backups? may|security records can)\b", clause)[0]
        if retention:
            core = re.split(r"\s+but\s+(?:keeping|retaining|preserving)\b|\s+except\b", core)[0]
        core = re.sub("|".join(BOILERPLATE), " ", core)
        cue = _first(EXPLICIT, core)
        if cue:
            if re.search(r"\b(?:if|unless|only after|maybe|perhaps|might)\b", core):
                uncertain = True
            else:
                yes.append(cue)
    past = re.search(r"\b(?:deleted|deleting|deletion|erased|closed|removed|account (?:page |itself )?is gone|profile is gone)\b", norm)
    review = re.search(r"\b(?:please|can you|could you).{0,100}\b(?:check|verify|audit|inspect|confirm|finish|investigate|handle|delete|erase|remove|clean)\b", norm)
    restore = re.search(NON_KINDS[0][1], norm)
    if not yes and not no and past and review and not re.search(QUESTION, norm):
        yes.append("prior_deletion_review")
    if uncertain or (yes and no) or (yes and restore and not re.search(r"\b(?:by mistake|accidentally)\b", norm)):
        return IntentResult(UNSURE, "conditional_or_conflicting", "", retention_allowed=True if retained else None)
    if restore:
        return IntentResult(NOT_APPLICABLE, "restoration_request", "", "restoration")
    if yes:
        return IntentResult(DELETION, "deletion_cue", yes[0], "deletion", True if retained else None)
    if no:
        kind = next((kind for kind, pattern in NON_KINDS if re.search(pattern, norm)), "question")
        return IntentResult(NOT_APPLICABLE, "explicit_refusal_or_scope", no[0], kind)
    for kind, pattern in NON_KINDS:
        if match := re.search(pattern, norm):
            return IntentResult(NOT_APPLICABLE, "non_deletion_request", match.group(0), kind)
    if re.search(QUESTION, norm):
        return IntentResult(NOT_APPLICABLE, "general_question", "", "question")
    return IntentResult(UNSURE, "quoted_or_ambiguous" if quoted else "no_reliable_rule", "")


FALLBACK_PROMPT = Path(__file__).resolve().parent / "prompts" / "intent_fallback_v3.md"

SCHEMA = {"type": "object", "additionalProperties": False,
    "required": ["label", "intent", "retention_allowed", "negated", "conditional", "spans"],
    "properties": {"label": {"enum": [DELETION, NOT_APPLICABLE, UNSURE]},
        "intent": {"enum": sorted(KINDS)}, "retention_allowed": {"type": ["boolean", "null"]},
        "negated": {"type": "boolean"}, "conditional": {"type": "boolean"},
        "spans": {"type": "array", "maxItems": 8, "items": {"type": "object", "additionalProperties": False,
            "required": ["start", "end"], "properties": {"start": {"type": "integer", "minimum": 0}, "end": {"type": "integer", "minimum": 1}}}}}}


def valid_assessment(answer, text):
    if type(answer) is not dict or set(answer) != set(SCHEMA["required"]): return False
    if answer["label"] not in (DELETION, NOT_APPLICABLE, UNSURE) or answer["intent"] not in KINDS: return False
    if any(type(answer[k]) is not bool for k in ("negated", "conditional")): return False
    if answer["retention_allowed"] is not None and type(answer["retention_allowed"]) is not bool: return False
    if type(answer["spans"]) is not list or len(answer["spans"]) > 8: return False
    for span in answer["spans"]:
        if type(span) is not dict or set(span) != {"start", "end"}: return False
        if type(span["start"]) is not int or type(span["end"]) is not int or not 0 <= span["start"] < span["end"] <= len(text): return False
    if answer["label"] == UNSURE: return answer["intent"] == "unknown"
    if not answer["spans"]: return False
    if answer["label"] == DELETION:
        return answer["intent"] == "deletion" and not (answer["negated"] or answer["conditional"])
    return answer["intent"] not in {"deletion", "unknown"}


def classify_with_fallback(text, llm=None):
    """Rules first; failed/missing/invalid classifications stay UNSURE."""
    result = classify(text)
    if result.label != UNSURE or llm is None or result.rule in {"parser_failure", "invalid_or_empty"}:
        return result
    try:
        template = FALLBACK_PROMPT.read_text(encoding="utf-8")
        version = re.search(r"prompt_version: (\S+)", template).group(1)
        prompt = template.replace("{schema_json}", json.dumps(SCHEMA, sort_keys=True)).replace("{message_json}", json.dumps(text, ensure_ascii=False))
        answer = llm.generate_json("intent_fallback", prompt, version, validate=lambda a: valid_assessment(a, text))
        if answer is None:
            return IntentResult(UNSURE, getattr(llm, "last_failure", None) or "model_unavailable", "")
        if not valid_assessment(answer, text): return IntentResult(UNSURE, "model_response_invalid", "")
        return IntentResult(answer["label"], "llm_fallback", "", answer["intent"], answer["retention_allowed"])
    except Exception:
        return IntentResult(UNSURE, "model_failure", "")
