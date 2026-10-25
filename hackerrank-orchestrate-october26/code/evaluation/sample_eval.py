"""Freeze predictions first; a separate command may then read public references."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_agent import AuditFailure, RunConfig, default_tools
from audit_agent.contracts import (CompilationInput, ExtractionInput, IndexInput, InvestigationInput,
                                   LoadInput, ValidationInput)
from audit_agent.model_schemas import canonical, digest


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_bytes():
    code = Path(__file__).resolve().parents[1]
    return {str(path.relative_to(code)).replace("\\", "/"): path.read_bytes()
            for path in sorted([code / "main.py", *(code / "audit_agent").glob("*.py"),
                                *(code / "audit_agent").glob("*.ps1"), *(code / "prompts").glob("*.md")])}


def predict(dataset: Path, run: Path, *, tools=None,
            requests_file="sample_deletion_requests.csv", expected_cases=32) -> dict:
    # No reference path is imported, hashed, opened or passed to the tools here.
    if run.exists():
        raise ValueError("Run directories are immutable")
    sources = source_bytes()
    run.mkdir(parents=True)
    config = RunConfig(dataset, run / "validated.csv", expected_cases=expected_cases,
                       requests_file=requests_file)
    tools = tools or default_tools()
    inputs = tools.load(LoadInput(config))
    failures, plans, investigations = [], [], []
    stage = "extract_evidence"
    try:
        evidence = tools.extract(ExtractionInput(inputs, config.max_observations))
        stage = "index_evidence"
        index = tools.index(IndexInput(inputs, evidence))
    except AuditFailure as error:
        failures = [{"case_id": request.case_id, "stage": stage, "failure_type": error.kind.value}
                    for request in inputs.requests]
    else:
        for request in inputs.requests:
            stage = "investigate"
            try:
                investigation = tools.investigate(InvestigationInput(request, inputs, index))
                stage = "compile_plan"
                plan = tools.compile(CompilationInput(investigation))
                stage = "validate_output"
                # Validate each candidate using the same production validator.
                tools.validate(ValidationInput(replace(inputs, requests=(request,)), index, (investigation,), (plan,)))
                plans.append(plan); investigations.append(investigation)
            except AuditFailure as error:
                failures.append({"case_id": request.case_id, "stage": stage, "failure_type": error.kind.value,
                                 "reason": error.reason.value if error.reason else None})
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["case_id", "deletion_status", "steps_json"])
    for plan in sorted(plans, key=lambda p: p.case_id):
        writer.writerow([plan.case_id, plan.deletion_status,
                         json.dumps([asdict(s) for s in plan.steps], sort_keys=True, separators=(",", ":"))])
    predictions = output.getvalue().encode("utf-8")
    (run / "predictions.csv").write_bytes(predictions)
    (run / "failures.json").write_bytes(canonical(failures))
    if source_bytes() != sources:
        raise ValueError("Prediction code changed during execution; run is not sealed")
    hashes = {}
    for relative, content in sources.items():
        target = run / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        hashes[relative] = sha(content)
    trace = [{"case_id": i.request.case_id, "authorized": i.authorized,
              "resources": [{"system_id": f.system_id, "resource_id": f.resource_id,
                  "source_id": f.source_id, "locator": f.locator, "state": f.state.value,
                  "copy_id": f.copy_id, "captured_at": f.captured_at.isoformat(),
                  "observed_at": f.observed_at.isoformat()} for f in i.resources]}
             for i in investigations]
    (run / "trace.json").write_bytes(canonical(trace))
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "case_ids": [r.case_id for r in inputs.requests],
        "predictions_sha256": sha(predictions), "failures_sha256": sha((run / "failures.json").read_bytes()),
        "source_sha256": digest(hashes), "source_files": hashes,
        "request_sha256": sha((dataset / requests_file).read_bytes()),
        "requests_file": requests_file,
        "predicted_cases": len(plans), "failed_cases": len(failures), "references_read": False,
        "failure_groups": dict(Counter(f["stage"] + ":" + (f.get("reason") or f["failure_type"]) for f in failures))}
    manifest["trace_sha256"] = sha((run / "trace.json").read_bytes())
    (run / "manifest.json").write_bytes(canonical(manifest))
    return manifest


def read_frozen(run: Path):
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    if sha((run / "predictions.csv").read_bytes()) != manifest["predictions_sha256"] or \
       sha((run / "failures.json").read_bytes()) != manifest["failures_sha256"]:
        raise ValueError("Frozen run modified")
    if manifest["source_sha256"] != digest(manifest["source_files"]) or any(
            not (run / "source" / name).resolve().is_relative_to((run / "source").resolve()) or
            sha((run / "source" / name).read_bytes()) != expected for name, expected in manifest["source_files"].items()):
        raise ValueError("Frozen prediction source modified")
    if "trace_sha256" in manifest and sha((run / "trace.json").read_bytes()) != manifest["trace_sha256"]:
        raise ValueError("Frozen reasoning trace modified")
    rows = list(csv.DictReader(io.StringIO((run / "predictions.csv").read_text(encoding="utf-8"))))
    predictions = {r["case_id"]: {"deletion_status": r["deletion_status"], "steps": json.loads(r["steps_json"])} for r in rows}
    failures = json.loads((run / "failures.json").read_text(encoding="utf-8"))
    if len(predictions) != len(rows) or len({f["case_id"] for f in failures}) != len(failures) or \
       set(predictions) & {f["case_id"] for f in failures} or \
       set(predictions) | {f["case_id"] for f in failures} != set(manifest["case_ids"]):
        raise ValueError("Incomplete run membership")
    return manifest, predictions, {f["case_id"]: f for f in failures}


def differences(actual, expected):
    # Match exact semantic identities before diagnosing individual field errors.
    # Residual correspondence is explicitly diagnostic, never prediction input.
    keys = ("phase", "system_id", "resource_id", "operation", "state", "evidence_id", "step_no")
    remaining_a, remaining_e = set(range(len(actual))), set(range(len(expected)))
    matched = []
    for identity in [("phase", "system_id", "resource_id", "operation"),
                     ("phase", "system_id", "operation"), ("phase", "system_id", "resource_id")]:
        for e in sorted(remaining_e):
            candidates = [a for a in remaining_a if all(actual[a].get(k) == expected[e].get(k) for k in identity)]
            if candidates:
                a = min(candidates, key=lambda n: (sum(actual[n].get(k) != expected[e].get(k) for k in keys), n))
                matched.append((e, a)); remaining_e.remove(e); remaining_a.remove(a)
    field_errors = [{"expected_index": e + 1, "actual_index": a + 1,
                     "fields": {k: {"expected": expected[e].get(k), "actual": actual[a].get(k)}
                                for k in keys if actual[a].get(k) != expected[e].get(k)}}
                    for e, a in sorted(matched) if actual[a] != expected[e]]
    positions = [a for e, a in sorted(matched)]
    matched_errors = sum(len(error["fields"]) for error in field_errors)
    exact_steps = sum(actual[a] == expected[e] for e, a in matched)
    return {"missing_steps": [expected[e] for e in sorted(remaining_e)],
            "extra_steps": [actual[a] for a in sorted(remaining_a)],
            "field_errors": field_errors, "order_error": positions != sorted(positions),
            "expected_steps": len(expected), "actual_steps": len(actual), "exact_steps": exact_steps,
            "correct_fields": len(matched) * len(keys) - matched_errors,
            "expected_fields": len(expected) * len(keys), "sequence_exact": actual == expected}


def compare(dataset: Path, run: Path, report: Path):
    manifest, predictions, failures = read_frozen(run)  # Verify freeze before reference access.
    if manifest.get("requests_file", "sample_deletion_requests.csv") != "sample_deletion_requests.csv":
        raise ValueError("Public references cannot score target requests")
    with (dataset / "sample_output.csv").open(encoding="utf-8-sig", newline="") as stream:
        reference = list(csv.DictReader(stream))
    if len(reference) != len(manifest["case_ids"]) or {r["case_id"] for r in reference} != set(manifest["case_ids"]):
        raise ValueError("Reference membership")
    cases = []
    for row in reference:
        case = row["case_id"]; expected = json.loads(row["steps_json"]); actual = predictions.get(case)
        diff = differences(actual["steps"] if actual else [], expected)
        diff["sequence_exact"] = actual is not None and diff["sequence_exact"]
        cases.append({"case_id": case, "expected_status": row["deletion_status"],
            "actual_status": actual["deletion_status"] if actual else None,
            "status_correct": actual is not None and actual["deletion_status"] == row["deletion_status"],
            "full_case_exact": actual is not None and actual["deletion_status"] == row["deletion_status"] and actual["steps"] == expected,
            "failure": failures.get(case), **diff})
    metrics = {"cases": len(cases), "predicted_cases": len(predictions),
        "status_correct": sum(c["status_correct"] for c in cases),
        "full_case_exact": sum(c["full_case_exact"] for c in cases)}
    metrics["status_accuracy"] = metrics["status_correct"] / len(cases)
    metrics["full_case_exact_accuracy"] = metrics["full_case_exact"] / len(cases)
    for key in ("expected_steps", "actual_steps", "exact_steps", "correct_fields", "expected_fields", "sequence_exact"):
        metrics[key] = sum(c[key] for c in cases)
    metrics["step_precision"] = metrics["exact_steps"] / metrics["actual_steps"] if metrics["actual_steps"] else 0
    metrics["step_recall"] = metrics["exact_steps"] / metrics["expected_steps"] if metrics["expected_steps"] else 0
    metrics["field_accuracy"] = metrics["correct_fields"] / metrics["expected_fields"] if metrics["expected_fields"] else 0
    assessment = {"metrics": metrics, "cases": cases, "frozen_sha256": manifest["predictions_sha256"]}
    (run / "comparison.json").write_bytes(canonical(assessment))
    lines = ["# Public sample comparison", "", "Predictions were frozen before this comparison read the reference file. Earlier conversation work inspected public examples, so this is not a blind evaluation.", "",
        f"Status accuracy: {metrics['status_correct']}/{len(cases)} ({metrics['status_accuracy']:.2%}).",
        f"Full-case exact accuracy: {metrics['full_case_exact']}/{len(cases)} ({metrics['full_case_exact_accuracy']:.2%}).",
        f"Prediction coverage: {len(predictions)}/{len(cases)}; execution failures remain failures, not invented statuses.", "",
        f"Exact-step precision/recall: {metrics['step_precision']:.2%} / {metrics['step_recall']:.2%}. Field accuracy: {metrics['field_accuracy']:.2%} (missing steps contribute zero correct fields). Exact sequences: {metrics['sequence_exact']}/{len(cases)}.", "",
        "| Case | Predicted | Reference | Status | Full case | Root failure / deltas |", "|---|---|---|---|---|---|"]
    for c in cases:
        failure = c["failure"]
        reason = (failure["stage"] + ":" + (failure.get("reason") or failure["failure_type"])) if failure else \
                 f"missing={len(c['missing_steps'])}, extra={len(c['extra_steps'])}, field errors={len(c['field_errors'])}, order={c['order_error']}"
        lines.append(f"| {c['case_id']} | {c['actual_status'] or 'NO PREDICTION'} | {c['expected_status']} | {c['status_correct']} | {c['full_case_exact']} | {reason} |")
    for c in cases:
        if not c["full_case_exact"]:
            lines += ["", f"## {c['case_id']}", "", "```json", json.dumps(c, ensure_ascii=False, indent=2), "```"]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return metrics


def compare_runs(before: Path, after: Path, *, architectural=False, explanations=None):
    """No references needed for byte preservation or complete prediction deltas."""
    old_manifest, old, old_failures = read_frozen(before)
    new_manifest, new, new_failures = read_frozen(after)
    if old_manifest["case_ids"] != new_manifest["case_ids"] or old_manifest["request_sha256"] != new_manifest["request_sha256"]:
        raise ValueError("Runs have different requests")
    identical = (before / "predictions.csv").read_bytes() == (after / "predictions.csv").read_bytes()
    failure_signature = lambda failures: {key: (f["stage"], f["failure_type"]) for key, f in failures.items()}
    if architectural and (not identical or failure_signature(old_failures) != failure_signature(new_failures)):
        raise ValueError("Architectural refactor changed prediction bytes or failure outcomes")
    changed = [case for case in old_manifest["case_ids"] if old.get(case) != new.get(case)]
    if not architectural and any(not explanations or not explanations.get(case) for case in changed):
        raise ValueError("Every changed prediction requires an explanation")
    return {"identical_bytes": identical, "changed_predictions": [
        {"case_id": case, "explanation": explanations[case], "before": old.get(case), "after": new.get(case),
         "step_delta": differences(new.get(case, {}).get("steps", []), old.get(case, {}).get("steps", []))}
        for case in changed]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["predict", "compare", "compare-runs"])
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parents[2] / "dataset")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--architectural", action="store_true")
    parser.add_argument("--explanations", type=Path)
    parser.add_argument("--requests-file", choices=["sample_deletion_requests.csv", "deletion_requests.csv"],
                        default="sample_deletion_requests.csv")
    parser.add_argument("--expected-cases", type=int, default=32)
    args = parser.parse_args()
    if args.command == "predict":
        result = predict(args.dataset, args.run, requests_file=args.requests_file, expected_cases=args.expected_cases)
        print(json.dumps({k: result[k] for k in ("predicted_cases", "failed_cases", "predictions_sha256", "failure_groups")}))
    elif args.command == "compare":
        if args.report is None:
            parser.error("--report required for comparison")
        print(json.dumps(compare(args.dataset, args.run, args.report)))
    else:
        if args.before is None: parser.error("--before required for run comparison")
        reasons = json.loads(args.explanations.read_text(encoding="utf-8")) if args.explanations else None
        result = compare_runs(args.before, args.run, architectural=args.architectural, explanations=reasons)
        if args.report:
            args.report.write_bytes(canonical(result))
        print(json.dumps({"identical_bytes": result["identical_bytes"], "changed_predictions": len(result["changed_predictions"])}))


if __name__ == "__main__":
    main()
