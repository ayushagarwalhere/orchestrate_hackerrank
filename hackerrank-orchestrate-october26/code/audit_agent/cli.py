"""CLI composition root. Default execution makes no model or network calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .agent import AuditAgent, default_tools
from .contracts import AuditFailure, FailureType, RunConfig
from .model_runtime import InferenceLimits, ModelRuntime, ResponseCache
from .telemetry import JsonlSink, Telemetry


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Bounded deletion audit; fail closed on incomplete evidence.")
    parser.add_argument("--dataset", type=Path, default=root / "dataset")
    parser.add_argument("--output", type=Path, default=root / "output.csv")
    parser.add_argument("--telemetry", type=Path, default=root / "runs" / "tool_outcomes.jsonl")
    parser.add_argument("--expected-cases", type=int, default=518,
                        help="Exact expected request count; use a smaller count only for independent fixtures.")
    parser.add_argument("--extractor", help=argparse.SUPPRESS)  # Retired unrestricted interface; fail closed.
    parser.add_argument("--allow-live", action="store_true", help="Explicitly allow bounded model calls on cache misses.")
    parser.add_argument("--model-client", metavar="MODULE:FACTORY", help="Trusted low-level ModelClient factory.")
    parser.add_argument("--inference-provider")
    parser.add_argument("--inference-model")
    parser.add_argument("--model-cache", type=Path, default=root / "runs" / "model-cache")
    parser.add_argument("--max-model-invocations", type=int, default=32)
    parser.add_argument("--max-live-calls", type=int, default=16)
    parser.add_argument("--model-retries", type=int, default=1)
    parser.add_argument("--model-timeout", type=float, default=20)
    parser.add_argument("--model-total-seconds", type=float, default=120)
    parser.add_argument("--max-model-tokens", type=int, default=100000)
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    args = parser.parse_args(argv)
    telemetry = None
    try:
        dataset, output, log = args.dataset.resolve(), args.output.resolve(), args.telemetry.resolve()
        if log.is_relative_to(dataset) or output.is_relative_to(dataset) or log == output or log.suffix != ".jsonl":
            raise AuditFailure(FailureType.INPUT)
        telemetry = Telemetry(JsonlSink(log))
        if args.extractor is not None:
            raise AuditFailure(FailureType.INPUT)
        runtime = None
        configured = bool(args.inference_provider or args.inference_model or args.model_client or args.allow_live)
        if configured:
            cache = args.model_cache.resolve()
            if (not args.inference_provider or not args.inference_model or cache.is_relative_to(dataset) or
                    cache in {output, log} or (args.allow_live and not args.model_client)):
                raise AuditFailure(FailureType.INPUT)
            runtime = ModelRuntime(args.inference_provider, args.inference_model, client=args.model_client,
                allow_live=args.allow_live, cache=ResponseCache(cache), limits=InferenceLimits(
                    max_invocations=args.max_model_invocations, max_live_calls=args.max_live_calls,
                    max_retries=args.model_retries, timeout_seconds=args.model_timeout,
                    total_seconds=args.model_total_seconds, max_total_tokens=args.max_model_tokens,
                    max_output_tokens=args.max_output_tokens))
        agent = AuditAgent(default_tools(model_runtime=runtime), telemetry)
        result = agent.run(RunConfig(dataset, output, args.expected_cases))
        print(json.dumps({"status": "published", "rows": result.rows, "sha256": result.sha256,
                          **telemetry.summary()}, sort_keys=True))
        return 0
    except Exception as error:
        kind = error.kind if isinstance(error, AuditFailure) else FailureType.INTERNAL
        stage = error.stage.value if isinstance(error, AuditFailure) and error.stage else None
        print(json.dumps({"status": "failed", "failure_type": kind.value, "tool": stage,
                          **(telemetry.summary() if telemetry else {})}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
