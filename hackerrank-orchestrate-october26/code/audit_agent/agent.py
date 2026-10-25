"""Actual coordinator: every CLI run goes through these seven narrow tools."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from .contracts import (COMPILE, EXTRACT, INDEX, INVESTIGATE, LOAD, PUBLISH, VALIDATE,
                        AuditFailure, CasePlan, CompilationInput, EvidenceIndex, ExtractedEvidence,
                        ExtractionInput, FailureType, IndexInput, Investigation, InvestigationInput,
                        LoadInput, LoadedInputs, OptionalExtractor, Publication, PublicationInput,
                        RunConfig, Tool, ToolContract, ValidatedOutput, ValidationInput)
from .extraction import ExtractEvidence
from .inputs import LoadInputs
from .investigation import IndexEvidence, Investigate
from .output import PublishOutput, ValidateOutput
from .planning import CompilePlan
from .telemetry import Telemetry
from .model_runtime import ModelRuntime


@dataclass(frozen=True)
class ToolSet:
    load: Tool[LoadInput, LoadedInputs]
    extract: Tool[ExtractionInput, ExtractedEvidence]
    index: Tool[IndexInput, EvidenceIndex]
    investigate: Tool[InvestigationInput, Investigation]
    compile: Tool[CompilationInput, CasePlan]
    validate: Tool[ValidationInput, ValidatedOutput]
    publish: Tool[PublicationInput, Publication]
    model_runtime: ModelRuntime | None = None


def default_tools(extractor: OptionalExtractor | None = None, model_runtime: ModelRuntime | None = None) -> ToolSet:
    from .model_adapters import ModelIntentInterpreter
    interpreter = ModelIntentInterpreter(model_runtime) if model_runtime is not None else None
    return ToolSet(LoadInputs(), ExtractEvidence(extractor, model_runtime), IndexEvidence(), Investigate(interpreter),
                   CompilePlan(), ValidateOutput(), PublishOutput(), model_runtime)


def counts_for(output) -> dict[str, int]:
    if type(output) is LoadedInputs:
        return {"requests": len(output.requests), "identities": len(output.identities),
                "activities": len(output.activities), "artifacts": len(output.artifacts)}
    if type(output) is ExtractedEvidence:
        return {"artifacts": len(output.processed_ids), "observations": len(output.observations),
                "external_calls": output.external_calls, "ownership_links": len(output.ownership_links),
                "inference_candidates": len(output.inference_candidates), "assumptions": len(output.assumptions),
                "evidence_gaps": len(output.gaps)}
    if type(output) is EvidenceIndex:
        return {"observations": len(output.observations), "index_keys": len(output.by_resource),
                "ownership_links": len(output.ownership_links)}
    if type(output) is Investigation:
        return {"requests": 1, "resources": len(output.resources), "ownership_links": len(output.ownership_links),
                "inference_candidates": len(output.inference_candidates), "assumptions": len(output.assumptions)}
    if type(output) is CasePlan:
        return {"rows": 1, "steps": len(output.steps)}
    if type(output) is ValidatedOutput:
        return {"rows": output.rows, "bytes": len(output.content)}
    if type(output) is Publication:
        return {"rows": output.rows, "bytes": output.bytes_written}
    raise AuditFailure(FailureType.CONTRACT)


I = TypeVar("I")
O = TypeVar("O")


class AuditAgent:
    def __init__(self, tools: ToolSet | None = None, telemetry: Telemetry | None = None):
        self.tools = tools if tools is not None else default_tools()
        self.telemetry = telemetry if telemetry is not None else Telemetry()

    def _call(self, tool: Tool[I, O], expected: ToolContract[I, O], value: I) -> O:
        start = self.telemetry.clock()
        try:
            if tool.contract != expected or type(value) is not expected.input_type:
                raise AuditFailure(FailureType.CONTRACT)
            output = tool(value)
            if type(output) is not expected.output_type:
                raise AuditFailure(FailureType.CONTRACT)
            counts = counts_for(output)
        except Exception as error:
            known = isinstance(error, AuditFailure) and type(error.kind) is FailureType
            kind = error.kind if known else FailureType.INTERNAL
            self.telemetry.record(expected.stage, "failure", start, error.counts if known else {}, kind)
            raise AuditFailure(kind, expected.stage, reason=error.reason if known else None) from None
        self.telemetry.record(expected.stage, "success", start, counts)
        return output

    def run(self, config: RunConfig) -> Publication:
        self.telemetry.start()
        if self.tools.model_runtime is not None:
            self.tools.model_runtime.begin_run()
        try:
            inputs = self._call(self.tools.load, LOAD, LoadInput(config))
            evidence = self._call(self.tools.extract, EXTRACT, ExtractionInput(inputs, config.max_observations))
            # Deliberately outside the case loop: the same immutable index object
            # is passed to every investigation and to final validation.
            index = self._call(self.tools.index, INDEX, IndexInput(inputs, evidence))
            investigations, plans = [], []
            for request in inputs.requests:
                investigation = self._call(self.tools.investigate, INVESTIGATE,
                                           InvestigationInput(request, inputs, index))
                investigations.append(investigation)
                plans.append(self._call(self.tools.compile, COMPILE, CompilationInput(investigation)))
            validated = self._call(self.tools.validate, VALIDATE,
                                   ValidationInput(inputs, index, tuple(investigations), tuple(plans)))
            result = self._call(self.tools.publish, PUBLISH, PublicationInput(config, validated))
        except Exception as error:
            kind = error.kind if isinstance(error, AuditFailure) else FailureType.INTERNAL
            if self.tools.model_runtime is not None:
                self.telemetry.model_usage = self.tools.model_runtime.summary()
            self.telemetry.finish(False, kind)
            raise
        if self.tools.model_runtime is not None:
            self.telemetry.model_usage = self.tools.model_runtime.summary()
        self.telemetry.finish(True)
        return result
