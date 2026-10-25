"""Independent plan checks and a single atomic publication effect."""
from __future__ import annotations

from dataclasses import asdict
import csv
import hashlib
import io
import os
import tempfile

from .contracts import (PUBLISH, VALIDATE, AuditFailure, FailureType, Publication, PublicationInput,
                        Step, ValidatedOutput, ValidationInput)
from .planning import OPERATIONS, obligations, step_order
from .identity import resolve_identity

HEADER = ["case_id", "deletion_status", "steps_json"]


class ValidateOutput:
    contract = VALIDATE

    def __call__(self, value: ValidationInput) -> ValidatedOutput:
        try:
            return self._validate(value)
        except Exception:
            raise AuditFailure(FailureType.VALIDATION) from None

    def _validate(self, value: ValidationInput) -> ValidatedOutput:
        import json
        expected = {r.case_id: r for r in value.inputs.requests}
        plans = {p.case_id: p for p in value.plans}
        investigations = {i.request.case_id: i for i in value.investigations}
        if (len(plans) != len(value.plans) or len(investigations) != len(value.investigations) or
                set(plans) != set(expected) or set(investigations) != set(expected)):
            raise ValueError()
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(HEADER)
        known_facts = set(value.index.observations)
        known_ownership = set(value.index.ownership_links)
        for case_id in sorted(expected):
            plan = plans[case_id]
            investigation = investigations[case_id]
            request = expected[case_id]
            if investigation.request != request or type(investigation.authorized) is not bool:
                raise ValueError()
            from .investigation import request_authorizes
            try:
                authorized = request_authorizes(request.request_text)
            except AuditFailure as error:
                if error.kind is not FailureType.UNRESOLVED or investigation.intent_assessment is None:
                    raise ValueError()
                from .model_adapters import validate_intent_assessment
                authorized = validate_intent_assessment(request, investigation.intent_assessment)
            if authorized != investigation.authorized:
                raise ValueError()
            if not investigation.authorized:
                if plan.deletion_status != "NOT_APPLICABLE" or plan.steps or investigation.resources:
                    raise ValueError()
            else:
                identity = resolve_identity(request, value.inputs)
                if any(g.captured_at <= request.audit_at and (not g.identifiers or
                       any(i.key in identity.keys for i in g.identifiers)) for g in value.index.gaps):
                    raise ValueError()
                if not investigation.ownership_links or any(
                    link not in known_ownership or link.identifier.key not in identity.keys or
                    max(link.captured_at, link.observed_at, link.available_at) > request.audit_at
                    for link in investigation.ownership_links):
                    raise ValueError()
                owned_keys = {link.key for link in investigation.ownership_links}
                # Follow only eligible, source-backed dependency edges; an
                # extraction candidate proposing ownership never enters here.
                pending = list(owned_keys)
                while pending:
                    key = pending.pop()
                    for n in value.index.by_resource.get(key, ()):
                        fact = value.index.observations[n]
                        if max(fact.captured_at, fact.observed_at, fact.available_at) <= request.audit_at:
                            for child in fact.downstream:
                                if child not in owned_keys:
                                    owned_keys.add(child)
                                    pending.append(child)
                if not investigation.resources or any(
                        f not in known_facts or f.key not in owned_keys or
                        max(f.captured_at, f.observed_at, f.available_at) > request.audit_at
                        for f in investigation.resources):
                    raise ValueError()
                required = obligations(investigation)
                incomplete = any(o.violated for o in required)
                if plan.deletion_status != ("INCOMPLETE" if incomplete else "COMPLETE"):
                    raise ValueError()
                expected_ops = {}
                for obligation in required:
                    expected_ops[("VERIFICATION", *obligation.key, obligation.verification)] = obligation
                    if obligation.violated:
                        expected_ops[("FINDING", *obligation.key, obligation.finding)] = obligation
                        expected_ops[("REMEDIATION", *obligation.key, obligation.remediation)] = obligation
                actual_ops = {(s.phase, s.system_id, s.resource_id, s.operation) for s in plan.steps}
                if actual_ops != set(expected_ops) or len(actual_ops) != len(plan.steps):
                    raise ValueError()
                for step in plan.steps:
                    obligation = expected_ops[(step.phase, step.system_id, step.resource_id, step.operation)]
                    needs_proof = step.phase == "FINDING" or not incomplete
                    if needs_proof:
                        candidates = [f for f in obligation.copies if f.evidence_id == step.evidence_id]
                        if not candidates or (step.phase == "FINDING" and not any(
                            f.state != obligation.desired for f in candidates
                        )) or (step.phase != "FINDING" and any(
                            f.state != obligation.desired for f in candidates
                        )):
                            raise ValueError()
                    elif step.evidence_id != "":
                        raise ValueError()
                # Recheck precedence at the validation boundary, independently of
                # whether a replaceable compiler enforced it.
                positions = {(s.system_id, s.resource_id): n for n, s in enumerate(plan.steps)
                             if s.phase == "REMEDIATION"}
                for fact in investigation.resources:
                    for child in fact.downstream:
                        if child in positions and fact.key in positions:
                            safety_control = fact.category in {"DATA_FLOW", "BACKUP_ARCHIVE"}
                            if (positions[fact.key] < positions[child]) != safety_control:
                                raise ValueError()
            if tuple(sorted(plan.steps, key=step_order)) != plan.steps:
                raise ValueError()
            for n, step in enumerate(plan.steps, 1):
                if (type(step) is not Step or type(step.step_no) is not int or step.step_no != n or
                        step.state != OPERATIONS[step.phase][step.operation] or
                        not all(isinstance(v, str) for k, v in asdict(step).items() if k != "step_no")):
                    raise ValueError()
            writer.writerow([case_id, plan.deletion_status,
                             json.dumps([asdict(s) for s in plan.steps], sort_keys=True,
                                        separators=(",", ":"), ensure_ascii=False, allow_nan=False)])
        content = output.getvalue().encode("utf-8")
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        rows = list(reader)
        if reader.fieldnames != HEADER or [r["case_id"] for r in rows] != sorted(expected):
            raise ValueError()
        for row in rows:
            if json.loads(row["steps_json"]) != [asdict(s) for s in plans[row["case_id"]].steps]:
                raise ValueError()
        return ValidatedOutput(content, len(rows), hashlib.sha256(content).hexdigest())


class PublishOutput:
    contract = PUBLISH

    def __call__(self, value: PublicationInput) -> Publication:
        temporary = None
        try:
            output, dataset = value.config.output.resolve(), value.config.dataset.resolve()
            validated = value.validated
            if (output.is_relative_to(dataset) or output.suffix != ".csv" or
                    validated.rows != value.config.expected_cases or
                    hashlib.sha256(validated.content).hexdigest() != validated.sha256):
                raise ValueError()
            output.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=".audit-", suffix=".tmp", dir=output.parent)
            with os.fdopen(fd, "wb") as stream:
                stream.write(validated.content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, output)
            temporary = None
            return Publication(validated.rows, len(validated.content), validated.sha256)
        except Exception:
            raise AuditFailure(FailureType.PUBLICATION) from None
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
