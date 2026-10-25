"""The two admitted model tasks. Code, never the model, binds final provenance."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import re
import struct

from .contracts import (Artifact, ArtifactExtraction, AuditFailure, FailureType, IntentAssessment,
                        LoadedInputs, Request, timestamp)
from .evidence import (Assumption, AssumptionCode, Identifier, IdentifierKind, ModelProvenance,
                       reference_identifier)
from .extraction import _summary_record
from .model_runtime import ModelRuntime, Purpose, default_prompts
from .model_schemas import digest, validate, INTENT_SCHEMA


def intent_value(request: Request, value: dict) -> bool:
    validate(value, INTENT_SCHEMA)
    for span in value["spans"]:
        start, end, text = span["start"], span["end"], span["text"]
        if not 0 <= start < end <= len(request.request_text) or request.request_text[start:end] != text:
            raise ValueError()
    if (not value["spans"] or value["action"] == "unknown" or not value["affirmed"] or
            value["negated"] or value["conditional"]):
        raise ValueError()
    return value["action"] == "delete_account"


def validate_intent_assessment(request: Request, assessment: IntentAssessment) -> bool:
    prompt = default_prompts()[Purpose.INTENT]
    provenance = assessment.model_provenance if type(assessment) is IntentAssessment else None
    if (type(assessment) is not IntentAssessment or assessment.source_id != request.case_id or
            assessment.message_sha256 != hashlib.sha256(request.request_text.encode("utf-8")).hexdigest() or
            assessment.prompt_version != prompt.version or type(provenance) is not ModelProvenance or
            provenance.source_id != request.case_id or provenance.content_sha256 != assessment.message_sha256 or
            provenance.captured_at != request.requested_at or provenance.prompt_version != prompt.version or
            provenance.prompt_sha256 != prompt.sha256 or provenance.schema_version != prompt.schema_version or
            provenance.schema_sha256 != digest(prompt.schema) or
            not re.fullmatch(r"[a-f0-9]{64}", provenance.response_sha256)):
        raise ValueError()
    body = {"action": assessment.action, "affirmed": assessment.affirmed,
        "negated": assessment.negated, "conditional": assessment.conditional,
        "spans": [{"start": s, "end": e, "text": t} for s, e, t in assessment.spans]}
    if provenance.response_sha256 != digest(body):
        raise ValueError()
    return intent_value(request, body)


class ModelIntentInterpreter:
    def __init__(self, runtime: ModelRuntime):
        self.runtime = runtime

    def interpret(self, request: Request) -> IntentAssessment:
        # Do not spend inference or override a deterministic answer. Known
        # conditional/quoted requests remain unresolved, not model-authorized.
        from .investigation import request_authorizes
        try:
            request_authorizes(request.request_text)
        except AuditFailure as error:
            if error.kind is not FailureType.UNRESOLVED:
                raise
        else:
            raise AuditFailure(FailureType.CONTRACT)
        if (len(request.request_text) > 16000 or re.search(r"\b(if|unless|maybe|perhaps|only|provided|marketing)\b", request.request_text, re.I)
                or '"' in request.request_text or "`" in request.request_text):
            raise AuditFailure(FailureType.UNRESOLVED)
        payload = request.request_text.encode("utf-8")
        response = self.runtime.request(Purpose.INTENT, payload, "text/plain", {
            "source_id": request.case_id, "message_sha256": hashlib.sha256(payload).hexdigest(),
            "captured_at": request.requested_at.isoformat()}, lambda value: intent_value(request, value))
        value = response.value
        provenance = ModelProvenance(request.case_id, hashlib.sha256(payload).hexdigest(), request.requested_at,
            response.provenance["prompt_version"], response.provenance["prompt_sha256"],
            response.provenance["schema_version"], response.response_sha256, response.provenance["schema_sha256"])
        return IntentAssessment(request.case_id, hashlib.sha256(payload).hexdigest(),
            response.provenance["prompt_version"], value["action"], value["affirmed"], value["negated"],
            value["conditional"], tuple((s["start"], s["end"], s["text"]) for s in value["spans"]), provenance)


class ScreenshotAdapter:
    def __init__(self, runtime: ModelRuntime):
        self.runtime = runtime

    def extract(self, artifact: Artifact, inputs: LoadedInputs, native_observations) -> ArtifactExtraction:
        if artifact.suffix != ".png":
            raise AuditFailure(FailureType.UNSUPPORTED)
        if (not artifact.content.startswith(b"\x89PNG\r\n\x1a\n") or len(artifact.content) < 24 or
                hashlib.sha256(artifact.content).hexdigest() != artifact.sha256):
            raise AuditFailure(FailureType.MALFORMED)
        width, height = struct.unpack(">II", artifact.content[16:24])
        if not (0 < width <= 20000 and 0 < height <= 20000 and width * height <= 20_000_000):
            raise AuditFailure(FailureType.MALFORMED)
        resources = {}
        for fact in native_observations:
            resources.setdefault(fact.resource_id, []).append((fact.system_id, fact.category, fact.available_at))
        for activity in inputs.activities:
            if activity.target_system and activity.resource_id:
                resources.setdefault(activity.resource_id, []).append((activity.target_system, None, activity.event_time))
        aliases = {}
        for identity in inputs.identities:
            for identifier in (*identity.identifiers, Identifier(IdentifierKind.USER_ID, identity.user_id)):
                if identifier.kind not in {IdentifierKind.NAME, IdentifierKind.UNKNOWN}:
                    aliases[identifier.key] = min(aliases.get(identifier.key, identity.updated_at), identity.updated_at)
        for change in inputs.changes:
            if change.field_name in {"email", "phone", "email_hash"}:
                for raw in (change.old_value, change.new_value):
                    if raw:
                        key = Identifier(IdentifierKind(change.field_name), raw).key
                        aliases[key] = min(aliases.get(key, change.event_time), change.event_time)
        categories = {rule.category for rule in inputs.rules} | {"DATA_FLOW"}
        context = {"resources": {r: sorted((s, c or "", t.isoformat()) for s, c, t in rows)
                                  for r, rows in resources.items()},
                   "identifiers": sorted((kind.value, raw, at.isoformat()) for (kind, raw), at in aliases.items()),
                   "categories": sorted(categories)}

        def bind_record(record):
            visible = record["visible_text"]
            for name, value in record.items():
                if name.endswith("_text") and name != "visible_text" and value is not None and (
                        not value or value not in visible):
                    raise ValueError()
            left, top, right, bottom = record["box"]
            if not 0 <= left < right <= width or not 0 <= top < bottom <= height:
                raise ValueError()
            resource = record["resource_text"]
            if resource not in resources:
                raise ValueError()  # No model-invented or image-only ungrounded ID admission.
            options = resources[resource]
            system = record["system_text"]
            if system is None:
                systems = {row[0] for row in options}
                if len(systems) != 1:
                    raise ValueError()
                system = next(iter(systems))
            options = [row for row in options if row[0] == system]
            if not options:
                raise ValueError()
            category = record["category_text"]
            if category is None:
                known = {row[1] for row in options if row[1] is not None}
                category = next(iter(known)) if len(known) == 1 else "UNKNOWN"
            elif category not in categories:
                raise ValueError()
            available = max(artifact.captured_at, min(row[2] for row in options))
            subject = record["subject_text"]
            if subject is not None:
                key = reference_identifier(subject).key
                if key not in aliases:
                    raise ValueError()
                available = max(available, aliases[key])
            observed = timestamp(record["observed_at_text"]) if record["observed_at_text"] else artifact.captured_at
            return system, resource, category, subject, observed, max(available, observed)

        def semantics(value):
            if not value["complete"]:
                raise ValueError()
            for record in value["records"]:
                bind_record(record)

        response = self.runtime.request(Purpose.SCREENSHOT, artifact.content, "image/png", {
            "source_id": artifact.file_id, "image_sha256": artifact.sha256,
            "captured_at": artifact.captured_at.isoformat(), "context_sha256": digest(context)}, semantics)
        provenance = ModelProvenance(artifact.file_id, artifact.sha256, artifact.captured_at,
            response.provenance["prompt_version"], response.provenance["prompt_sha256"],
            response.provenance["schema_version"], response.response_sha256, response.provenance["schema_sha256"])
        observations, links, assumptions = [], [], []
        for n, record in enumerate(response.value["records"]):
            system, resource, category, subject, observed, available = bind_record(record)
            row = {"recorded_at": observed.isoformat(), "system": system, "resource_id": resource,
                   "record_type": category, "result": record["result_text"], "subject_reference": subject}
            bundle = _summary_record(artifact, row, f"model/records/{n}", available)
            observations.extend(replace(fact, model_provenance=provenance) for fact in bundle.observations)
            links.extend(replace(link, model_provenance=provenance) for link in bundle.ownership_links)
            assumptions.extend(bundle.assumptions)
            assumptions.append(Assumption(AssumptionCode.SCREENSHOT_TRANSCRIPTION, artifact.file_id,
                                           f"model/records/{n}", (system, resource)))
            if record["observed_at_text"] is None:
                assumptions.append(Assumption(AssumptionCode.SCREENSHOT_CAPTURE_TIME, artifact.file_id,
                                               f"model/records/{n}", (system, resource)))
        return ArtifactExtraction(artifact.file_id, artifact.sha256, tuple(observations), True,
                                  tuple(links), assumptions=tuple(assumptions))
