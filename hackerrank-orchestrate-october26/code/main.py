"""Ghost Data Still Exists — deletion-audit agent entry point.

    uv run python code/main.py [--data dataset] [--out output.csv]

AuditAgent coordinates typed tools; policy.py remains responsible for decisions
and ordering. Public sample inputs participate in joint workflow assignment;
reference answers are read only by the separate evaluation entry point.

Execution is offline by default. --enable-model explicitly enables optional Gemini
extraction and ambiguous-intent classification. --trace writes aggregate tool
events. A candidate must validate before it replaces the previous output.
"""

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_agent import AuditAgent  # noqa: E402
from audit_tools import case_number  # noqa: E402,F401 (backward-compatible import)
from llm import CACHE_DIR, default_llm  # noqa: E402


def usage_summary(llm, requests_count):
    """Live calls of this run plus the recorded usage of every cached answer the run relies on."""
    cached = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(CACHE_DIR).glob("*.json"))]
    by_task = {}
    for c in cached:
        t = by_task.setdefault((c["provider"], c["model"], c["task"]), {"answers": 0, "input_tokens": 0, "output_tokens": 0})
        t["answers"] += 1
        t["input_tokens"] += c["usage"]["input_tokens"]
        t["output_tokens"] += c["usage"]["output_tokens"]
    price_in = float(os.environ.get("LLM_PRICE_INPUT_PER_MTOK", "0") or 0)
    price_out = float(os.environ.get("LLM_PRICE_OUTPUT_PER_MTOK", "0") or 0)
    for v in by_task.values():
        v["cost_usd"] = round(v["input_tokens"] / 1e6 * price_in + v["output_tokens"] / 1e6 * price_out, 6)
    return {"requests": requests_count, "this_run": llm.meter.summary(),
            "prices_usd_per_mtok": {"input": price_in, "output": price_out},
            "cached_answers": [{"provider": p, "model": m, "task": t, **v} for (p, m, t), v in sorted(by_task.items())]}


def run(data_dir, out_path, use_llm=False, trace_path=None, ledger_path=None):
    """Compatibility entry point used by evaluation and terminal execution."""
    started = time.perf_counter()
    llm = default_llm() if use_llm else None
    agent = AuditAgent(llm=llm)
    rows = agent.run(Path(data_dir), Path(out_path), trace_path=trace_path, ledger_path=ledger_path)
    diagnostics = list(agent.trace.diagnostic_errors)
    if llm is not None:
        from audit_artifacts import atomic_json
        try:
            atomic_json(CACHE_DIR.parent / "usage_last_run.json", usage_summary(llm, len(rows)))
        except Exception:
            diagnostics.append('usage_write_failed')
    if diagnostics:
        print("Published CSV; diagnostic warnings: " + ",".join(diagnostics), file=sys.stderr)
    status = Counter(s for _, s, _ in rows)
    print(f"wrote {len(rows)} rows to {out_path} in {time.perf_counter() - started:.1f}s; status {dict(sorted(status.items()))}")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data", default=str(ROOT / "dataset"), help="dataset directory")
    parser.add_argument("--out", default=str(ROOT / "output.csv"), help="output CSV path")
    model_options = parser.add_mutually_exclusive_group()
    model_options.add_argument("--no-llm", action="store_true", help="use deterministic rules and validated cached facts only")
    model_options.add_argument("--enable-model", action="store_true", help="explicitly authorize the configured bounded fact/intent adapter")
    parser.add_argument("--trace", type=Path, help="write an aggregate tool execution trace outside dataset/")
    parser.add_argument("--ledger", type=Path, help="write detailed source observations and extraction outcomes outside dataset/; may contain customer text")
    args = parser.parse_args()
    run(Path(args.data), Path(args.out), use_llm=args.enable_model, trace_path=args.trace, ledger_path=args.ledger)


if __name__ == "__main__":
    main()
