"""Isolated negative controls for workflow tie-breaking; never a CLI profile.

Predict freezes every candidate before compare is allowed to open references.
Ordering alone does not establish ownership, regardless of the measured score.
The production workflow module is restored after every experimental run.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from audit_tools import AuditTools
from identity import parse_ts
from policy import case_number, serialize, steps_for
import workflow


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode_rows(rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["case_id", "deletion_status", "steps_json"])
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def ranks_for(strategy, requests, baseline, original_number):
    def order(request):
        cid = request["case_id"]
        at = parse_ts(request["requested_at"]).timestamp()
        if strategy == "latest_request_first":
            return -at, case_number(cid)
        if strategy == "earliest_request_first":
            return at, case_number(cid)
        subject = baseline[cid].subject
        return original_number(subject.user_id) if subject else original_number(cid), case_number(cid)
    return {r["case_id"]: n for n, r in enumerate(sorted(requests, key=order))}


def predict(data, run, repeats=3):
    """Uses participant inputs only; candidate CSVs never replace output.csv."""
    if run.exists() or run.resolve().is_relative_to(data.resolve()):
        raise ValueError("Use a new run directory outside dataset")
    if type(repeats) is not int or not 1 <= repeats <= 5:
        raise ValueError("Repeats must be between one and five")
    run.mkdir(parents=True)
    code = ROOT / "code"
    sources = [*code.glob("*.py"), *(code / "evidence").glob("*.py"),
               *(code / "prompts").glob("*.md"), *(code / "llm_cache/image_facts").glob("*.json"),
               Path(__file__).resolve()]
    source_bytes = {p.relative_to(code).as_posix(): p.read_bytes() for p in sources}
    tools = AuditTools()
    started = time.perf_counter()
    inputs = tools.load_inputs(data)
    index = tools.index_evidence(data)
    setup_seconds = time.perf_counter() - started
    original_number = workflow._number
    baseline = None
    records = []
    strategies = ("baseline", "latest_request_first", "earliest_request_first", "stable_subject_order")
    for strategy in strategies:
        timings = []
        record = {"strategy": strategy, "ownership_supported_by_order": False}
        ranks = {} if strategy == "baseline" else ranks_for(strategy, inputs.requests, baseline, original_number)
        try:
            previous = None
            for _ in range(repeats):
                workflow._number = original_number if strategy == "baseline" else lambda key: ranks.get(key, original_number(key))
                started = time.perf_counter()
                cases = tools.investigate(data, inputs, index, None)
                target_bytes = encode_rows(tools.compile_plan(inputs, cases))
                all_bytes = encode_rows((r["case_id"], cases[r["case_id"]].status,
                                         serialize(steps_for(cases[r["case_id"]]))) for r in inputs.requests)
                timings.append(time.perf_counter() - started)
                if previous is not None and previous != (target_bytes, all_bytes):
                    raise ValueError("Candidate is not deterministic")
                previous = target_bytes, all_bytes
                if strategy == "baseline":
                    baseline = cases
            target_path = run / (strategy + "_518.csv")
            all_path = run / (strategy + "_550.csv")
            target_path.write_bytes(target_bytes)
            all_path.write_bytes(all_bytes)
            errors, count = tools.validate(target_path, data)
            record.update(outcome="produced", target_rows=count, validation_errors=len(errors),
                          target_file=target_path.name, all_file=all_path.name,
                          target_sha256=digest(target_bytes), all_sha256=digest(all_bytes),
                          median_investigation_seconds=statistics.median(timings), repeat_seconds=timings)
        except Exception as error:
            record.update(outcome="failed", failure_type=type(error).__name__)
            if strategy == "baseline":
                raise
        finally:
            workflow._number = original_number
        records.append(record)
    if {name: (code / name).read_bytes() for name in source_bytes} != source_bytes:
        raise ValueError("Source changed during the experiment")
    for name, content in source_bytes.items():
        destination = run / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    manifest = {"references_read": False, "index_constructions": 1, "hosted_calls": 0,
                "load_and_index_seconds": setup_seconds, "candidates": records,
                "source_sha256": {name: digest(content) for name, content in source_bytes.items()}}
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def compare(data, run):
    """All answer access is confined to this post-freeze comparison command."""
    from evaluation.score import load_answers, score
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["source_sha256"].items():
        path = (run / "source" / name).resolve()
        if not path.is_relative_to((run / "source").resolve()) or digest(path.read_bytes()) != expected:
            raise ValueError("Frozen source changed")
    produced = [r for r in manifest["candidates"] if r["outcome"] == "produced"]
    for record in produced:
        for key in ("target", "all"):
            path = (run / record[key + "_file"]).resolve()
            if not path.is_relative_to(run.resolve()) or digest(path.read_bytes()) != record[key + "_sha256"]:
                raise ValueError("Frozen predictions changed")
    baseline = load_answers(run / produced[0]["target_file"])
    expected = load_answers(data / "sample_output.csv")
    results = []
    for record in produced:
        target = load_answers(run / record["target_file"])
        if baseline.keys() != target.keys():
            raise ValueError("Candidate target membership differs")
        metrics = score(expected, load_answers(run / record["all_file"]))
        changed = [{"case_id": cid, "before": baseline[cid], "after": target[cid]}
                   for cid in sorted(target, key=case_number) if target[cid] != baseline[cid]]
        results.append({"strategy": record["strategy"], "sample_metrics": metrics,
                        "target_rows_compared": len(target), "changed_targets": changed,
                        "target_status_changes": sum(c["before"][0] != c["after"][0] for c in changed),
                        "ownership_supported_by_order": False,
                        "median_investigation_seconds": record["median_investigation_seconds"],
                        "validation_errors": record["validation_errors"]})
    result = {"load_and_index_seconds": manifest["load_and_index_seconds"], "results": results,
              "failed_controls": [r for r in manifest["candidates"] if r["outcome"] == "failed"]}
    (run / "comparison.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["predict", "compare"])
    parser.add_argument("--data", type=Path, default=ROOT / "dataset")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.command == "predict":
        result = predict(args.data, args.run, args.repeats)
        print(json.dumps({k: result[k] for k in ("index_constructions", "hosted_calls", "candidates")}))
    else:
        result = compare(args.data, args.run)
        print(json.dumps([{"strategy": r["strategy"], "sample_status": r["sample_metrics"]["status_accuracy"],
                           "sample_exact": r["sample_metrics"]["sequence_exact"],
                           "changed_targets": len(r["changed_targets"]), "target_status_changes": r["target_status_changes"],
                           "median_seconds": r["median_investigation_seconds"]} for r in result["results"]]))


if __name__ == "__main__":
    main()
