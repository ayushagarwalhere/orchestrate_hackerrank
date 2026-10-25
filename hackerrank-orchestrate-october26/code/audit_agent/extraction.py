"""Typed extraction: readings, ownership links and interpretations stay separate."""
from __future__ import annotations

import json
import re
from datetime import datetime

from .contracts import (EXTRACT, Artifact, ArtifactExtraction, AuditFailure, ExtractedEvidence,
                        ExtractionInput, FailureType, Observation, OptionalExtractor, State, timestamp)
from .evidence import (Assumption, AssumptionCode, EvidenceBundle, EvidenceGap, EvidenceScope, FieldFact,
                       FieldPresence, Identifier, IdentifierKind, InferenceCandidate, InferenceKind,
                       ModelProvenance, OwnershipBasis, OwnershipLink, Permission, PermissionFact, ScopeKind,
                       reference_identifier)

RESULTS = {"FOUND": State.PRESENT, "NOT_FOUND": State.ABSENT, **{s.value: s for s in State}}
CONDITIONS = frozenset({"shared_context", "subject_only", "active_hold", "restore_blockable",
                       "tombstone_reference_required"})
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,199}\Z")


class UnsupportedArtifact(Exception):
    pass


def _times_valid(artifact, captured, observed, available):
    return (all(type(t) is datetime and t.tzinfo is not None for t in (captured, observed, available)) and
            captured == artifact.captured_at and available >= max(captured, observed))


def validate_observations(artifact: Artifact, observations: tuple[Observation, ...]) -> None:
    if type(observations) is not tuple:
        raise AuditFailure(FailureType.MALFORMED)
    for fact in observations:
        if type(fact) is not Observation:
            raise AuditFailure(FailureType.MALFORMED)
        if (fact.source_id != artifact.file_id or not isinstance(fact.locator, str) or not fact.locator or
                not all(isinstance(x, str) and IDENTIFIER.fullmatch(x) for x in
                        (fact.system_id, fact.resource_id, fact.category, fact.copy_id)) or
                type(fact.state) is not State or not _times_valid(artifact, fact.captured_at,
                    fact.observed_at, fact.available_at) or
                type(fact.conditions) is not tuple or set(fact.conditions) - CONDITIONS or
                (fact.retention_until is not None and
                 (type(fact.retention_until) is not datetime or fact.retention_until.tzinfo is None)) or
                type(fact.downstream) is not tuple or any(
                    type(edge) is not tuple or len(edge) != 2 or
                    any(not isinstance(x, str) or not IDENTIFIER.fullmatch(x) for x in edge)
                    for edge in fact.downstream)):
            raise AuditFailure(FailureType.MALFORMED)
        scope = fact.scope
        if (type(scope) is not EvidenceScope or type(scope.kind) is not ScopeKind or
                type(scope.covered_tables) is not tuple or any(not isinstance(t, str) or not t for t in scope.covered_tables) or
                (scope.table is not None and (not isinstance(scope.table, str) or not scope.table)) or
                (scope.kind is ScopeKind.RESOURCE_LOOKUP and (scope.table is not None or scope.covered_tables)) or
                (scope.kind is ScopeKind.DATABASE_QUERY and fact.state is State.ABSENT and
                 (scope.table is None or scope.table not in scope.covered_tables))):
            raise AuditFailure(FailureType.MALFORMED)
        if (type(fact.fields) is not tuple or any(type(f) is not FieldFact or
                type(f.presence) is not FieldPresence or not f.name or
                (f.presence is not FieldPresence.VALUE and f.value is not None) or
                (f.presence is FieldPresence.VALUE and not isinstance(f.value, str)) for f in fact.fields) or
                type(fact.permissions) is not tuple or any(type(p) is not PermissionFact or
                not p.name or type(p.value) is not Permission for p in fact.permissions)):
            raise AuditFailure(FailureType.MALFORMED)
        if (len({f.name for f in fact.fields}) != len(fact.fields) or
                len({p.name for p in fact.permissions}) != len(fact.permissions)):
            raise AuditFailure(FailureType.MALFORMED)
        _validate_model_provenance(artifact, fact.model_provenance)


def _validate_model_provenance(artifact, provenance):
    if provenance is not None and (type(provenance) is not ModelProvenance or
            provenance.source_id != artifact.file_id or provenance.content_sha256 != artifact.sha256 or
            provenance.captured_at != artifact.captured_at or
            not all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in
                    (provenance.prompt_sha256, provenance.response_sha256, provenance.schema_sha256)) or
            not provenance.prompt_version or not provenance.schema_version):
        raise AuditFailure(FailureType.MALFORMED)


def validate_bundle(artifact: Artifact, bundle: EvidenceBundle) -> None:
    validate_observations(artifact, bundle.observations)
    if not all(type(items) is tuple for items in
               (bundle.ownership_links, bundle.inference_candidates, bundle.assumptions, bundle.gaps)):
        raise AuditFailure(FailureType.MALFORMED)
    for gap in bundle.gaps:
        if (type(gap) is not EvidenceGap or gap.source_id != artifact.file_id or not gap.locator or
                gap.captured_at != artifact.captured_at or type(gap.identifiers) is not tuple or
                any(type(i) is not Identifier or type(i.kind) is not IdentifierKind or
                    not isinstance(i.raw, str) or not i.raw.strip() for i in gap.identifiers)):
            raise AuditFailure(FailureType.MALFORMED)
    for link in bundle.ownership_links:
        if (type(link) is not OwnershipLink or link.source_id != artifact.file_id or not link.locator or
                not all(isinstance(x, str) and IDENTIFIER.fullmatch(x) for x in link.key) or
                type(link.identifier) is not Identifier or type(link.identifier.kind) is not IdentifierKind or
                not isinstance(link.identifier.raw, str) or not link.identifier.raw.strip() or
                type(link.basis) is not OwnershipBasis or not _times_valid(artifact, link.captured_at,
                    link.observed_at, link.available_at)):
            raise AuditFailure(FailureType.MALFORMED)
        _validate_model_provenance(artifact, link.model_provenance)
    for candidate in bundle.inference_candidates:
        if (type(candidate) is not InferenceCandidate or type(candidate.kind) is not InferenceKind or
                (candidate.proposed_state is not None and type(candidate.proposed_state) is not State) or
                type(candidate.resource_key) is not tuple or len(candidate.resource_key) != 2 or
                any(not isinstance(x, str) or not IDENTIFIER.fullmatch(x) for x in candidate.resource_key) or
                type(candidate.support) is not tuple or not candidate.support or
                any(type(ref) is not tuple or len(ref) != 2 or ref[0] != artifact.file_id or
                    not isinstance(ref[1], str) or not ref[1] for ref in candidate.support) or
                type(candidate.assumptions) is not tuple or
                any(type(code) is not AssumptionCode for code in candidate.assumptions)):
            raise AuditFailure(FailureType.MALFORMED)
    for assumption in bundle.assumptions:
        if (type(assumption) is not Assumption or type(assumption.code) is not AssumptionCode or
                assumption.source_id != artifact.file_id or not assumption.locator):
            raise AuditFailure(FailureType.MALFORMED)


def _field(row: dict, name: str) -> FieldFact:
    if name not in row:
        return FieldFact(name, FieldPresence.MISSING)
    if row[name] is None:
        return FieldFact(name, FieldPresence.NULL)
    return FieldFact(name, FieldPresence.VALUE, json.dumps(row[name], ensure_ascii=False, sort_keys=True))


def _summary_record(artifact: Artifact, row: dict, locator: str, outer_time: datetime) -> EvidenceBundle:
    required = {"recorded_at", "system", "resource_id", "record_type"}
    optional = {"result", "subject_reference", "conditions", "retention_until", "copy_id", "downstream",
                "scope", "restore_allowed", "enabled"}
    if not isinstance(row, dict) or not required <= row.keys() or row.keys() - required - optional:
        raise UnsupportedArtifact()
    observed = timestamp(row["recorded_at"])
    available = max(artifact.captured_at, outer_time, observed)
    raw_scope = row.get("scope")
    scope = EvidenceScope()
    if raw_scope is not None:
        if not isinstance(raw_scope, dict) or set(raw_scope) - {"kind", "table", "covered_tables"}:
            raise ValueError()
        scope = EvidenceScope(ScopeKind(raw_scope["kind"]), raw_scope.get("table"),
                              tuple(raw_scope.get("covered_tables", ())))
    permissions = []
    for name in ("restore_allowed", "enabled"):
        value = row.get(name)
        if value is not None and type(value) is not bool:
            raise ValueError()
        permissions.append(PermissionFact(name, Permission.UNKNOWN if value is None else
                                          Permission.ALLOWED if value else Permission.DENIED))
    fields = tuple(_field(row, name) for name in sorted(required | optional))
    fact = Observation(artifact.file_id, locator, row["system"], row["resource_id"], row["record_type"],
                       RESULTS.get(row.get("result"), State.UNKNOWN), artifact.captured_at, observed, available,
                       row.get("copy_id", "logical"), tuple(row.get("conditions") or ()),
                       timestamp(row["retention_until"]) if row.get("retention_until") else None,
                       tuple(tuple(edge) for edge in row.get("downstream", ())), scope, fields, tuple(permissions))
    assumptions = [Assumption(AssumptionCode.SUMMARY_READBACK, artifact.file_id, locator, fact.key)]
    if "copy_id" not in row:
        assumptions.append(Assumption(AssumptionCode.LOGICAL_COPY_SCOPE, artifact.file_id, locator, fact.key))
    if raw_scope is None:
        assumptions.append(Assumption(AssumptionCode.RESOURCE_COVERAGE, artifact.file_id, locator, fact.key))
    links, candidates = [], []
    reference = row.get("subject_reference")
    if reference and reference != "no direct identifier":
        identifier = reference_identifier(reference)
        if identifier.kind is IdentifierKind.UNKNOWN:
            candidates.append(InferenceCandidate(InferenceKind.UNCLASSIFIED_REFERENCE, fact.key,
                                                  ((artifact.file_id, locator),)))
        else:
            links.append(OwnershipLink(artifact.file_id, locator, *fact.key, identifier,
                                       artifact.captured_at, observed, available))
            assumptions.append(Assumption(AssumptionCode.REFERENCE_NAMING, artifact.file_id, locator, fact.key))
    return EvidenceBundle((fact,), tuple(links), tuple(candidates), tuple(assumptions))


def _merge(bundles) -> EvidenceBundle:
    bundles = tuple(bundles)
    return EvidenceBundle(*(tuple(item for bundle in bundles for item in getattr(bundle, name))
                            for name in ("observations", "ownership_links", "inference_candidates", "assumptions", "gaps")))


def native_extract(artifact: Artifact) -> EvidenceBundle:
    if artifact.suffix == ".json":
        data = json.loads(artifact.content.decode("utf-8-sig"))
        if not isinstance(data, dict) or set(data) != {"exported_at", "origin", "record_count", "records"}:
            if isinstance(data, dict) and any(key in data for key in ("snapshots", "service_exports", "collection")):
                from .readbacks import json_evidence
                return json_evidence(artifact)
            raise UnsupportedArtifact()
        if (not isinstance(data["records"], list) or type(data["record_count"]) is not int or
                len(data["records"]) != data["record_count"]):
            raise ValueError()
        outer = timestamp(data["exported_at"])
        return _merge(_summary_record(artifact, row, f"/records/{n}", outer)
                      for n, row in enumerate(data["records"]))
    if artifact.suffix == ".txt":
        lines = artifact.content.decode("utf-8-sig").splitlines()
        if not lines or lines[0] != "CUSTOMER PLATFORM - SHIFT HANDOVER":
            raise UnsupportedArtifact()
        bundles = []
        for n, line in enumerate(lines, 1):
            if not line.startswith("- "):
                continue
            values = line[2:].split(" | ")
            if len(values) != 6:
                raise ValueError()
            row = dict(zip(("recorded_at", "system", "resource_id", "record_type", "result", "subject_reference"), values))
            bundles.append(_summary_record(artifact, row, f"line:{n}", artifact.captured_at))
        if not bundles:
            raise ValueError()
        return _merge(bundles)
    if artifact.suffix == ".sql":
        from .readbacks import sql_evidence
        return sql_evidence(artifact)
    if artifact.suffix == ".log":
        from .readbacks import log_evidence
        return log_evidence(artifact)
    raise UnsupportedArtifact()


class ExtractEvidence:
    contract = EXTRACT

    def __init__(self, extractor: OptionalExtractor | None = None, model_runtime=None):
        self.extractor = extractor
        self.model_runtime = model_runtime

    def __call__(self, value: ExtractionInput) -> ExtractedEvidence:
        bundles, processed, calls = [], set(), 0
        facts_count = 0
        try:
            rank = {".json": 0, ".txt": 0, ".log": 1, ".sql": 2, ".pdf": 3, ".png": 4}
            for artifact in sorted(value.inputs.artifacts, key=lambda a: rank.get(a.suffix, 5)):
                try:
                    bundle = native_extract(artifact)
                except UnsupportedArtifact:
                    if self.model_runtime is not None and artifact.suffix == ".png":
                        from .model_adapters import ScreenshotAdapter
                        calls += 1
                        packet = ScreenshotAdapter(self.model_runtime).extract(artifact, value.inputs,
                            tuple(f for bundle in bundles for f in bundle.observations))
                    elif artifact.suffix == ".pdf" or (artifact.suffix == ".png" and
                            artifact.content.startswith(b"\x89PNG\r\n\x1a\n") and len(artifact.content) >= 24 and
                            int.from_bytes(artifact.content[16:20], "big") >= 10 and
                            int.from_bytes(artifact.content[20:24], "big") >= 10):
                        from .readbacks import media_evidence
                        media = media_evidence(artifact, tuple(f for b in bundles for f in b.observations))
                        packet = ArtifactExtraction(artifact.file_id, artifact.sha256, media.observations, True,
                            media.ownership_links, media.inference_candidates, media.assumptions, media.gaps)
                    elif self.extractor is None:
                        raise AuditFailure(FailureType.UNSUPPORTED) from None
                    else:
                        # In-process injection is for trusted deterministic
                        # adapters/tests. The CLI exposes only ModelRuntime.
                        calls += 1
                        try:
                            packet = self.extractor.extract(artifact)
                        except Exception:
                            raise AuditFailure(FailureType.PROVIDER) from None
                    if (type(packet) is not ArtifactExtraction or packet.artifact_id != artifact.file_id or
                            packet.artifact_sha256 != artifact.sha256 or type(packet.complete) is not bool):
                        raise AuditFailure(FailureType.MALFORMED)
                    if not packet.complete:
                        raise AuditFailure(FailureType.COVERAGE)
                    bundle = EvidenceBundle(packet.observations, packet.ownership_links,
                                            packet.inference_candidates, packet.assumptions, packet.gaps)
                validate_bundle(artifact, bundle)
                bundles.append(bundle)
                facts_count += len(bundle.observations)
                if sum(len(b.observations) + len(b.ownership_links) + len(b.inference_candidates) + len(b.assumptions) + len(b.gaps)
                       for b in bundles) > value.max_observations:
                    raise AuditFailure(FailureType.EXTRACTION)
                processed.add(artifact.file_id)
            merged = _merge(bundles)
            return ExtractedEvidence(merged.observations, frozenset(processed), calls,
                                     merged.ownership_links, merged.inference_candidates, merged.assumptions, merged.gaps)
        except Exception as error:
            kind = error.kind if isinstance(error, AuditFailure) else FailureType.MALFORMED
            raise AuditFailure(kind, counts={"artifacts": len(processed), "observations": facts_count,
                                             "external_calls": calls}) from None
