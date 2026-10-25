# Guarded search for a sample accuracy improvement

No evidence-supported improvement was promoted. The default remains **32/32 public statuses and 29/32 full-case exact cases**. The production CLI was independently rerun and all 518 rows remain byte-identical to output.csv. Hidden target accuracy cannot be measured locally; changed target answers cannot be certified as improvements from public scores alone.

## Frozen experiment results

Every strategy generated all 550 target/public predictions before the separate comparison command opened public answers. Earlier public examples were known, so this is not blind evaluation. These are negative controls for arbitrary ordering, not ownership evidence. All strategies passed the existing 518-row output validator; schema validity did not establish correct ownership.

| Tie priority | Status correct / 32 | Full-case exact / 32 | Changed target cases / 518 | Target status changes | Median investigation/compilation seconds |
|---|---:|---:|---:|---:|---:|
| baseline | 32 | 29 | 0 | 0 | 2.156 |
| latest_request_first | 32 | 27 | 3 | 0 | 2.310 |
| earliest_request_first | 32 | 24 | 121 | 0 | 2.175 |
| stable_subject_order | 32 | 28 | 1 | 0 | 2.258 |

**Latest-request-first fixes case_23, but breaks case_03, case_25 and case_26.** It also changes target cases case_44, case_547 and case_549. Its overall exact accuracy falls to 27/32. Selecting it just for the troublesome sample cohort would be an unsupported sample-specific correction. No such selection rule was added.

Earliest-request-first fixes no original mismatch and regresses cases 25, 26, 27, 28 and 29, changing 121 target cases. Stable-subject-order fixes no original mismatch, regresses case_03 and changes target case_44. All controls are rejected. See [accuracy_search_deltas.md](accuracy_search_deltas.md) for every changed target prediction and seven-field/ordering diagnostics.

## Runtime and isolation

The index was built **once**, with load/index time 2.012 seconds, and reused for every strategy and repetition. Each median covers three investigation/plan-compilation/serialization runs over all 550 requests with the same index. File validation and publication are outside those measured intervals. The timings are sequential observations on one host, not a statistically controlled performance benchmark. Small timing differences do not establish a speedup or a reliable slowdown. No live model calls were made.

The production CLI was separately run with --no-llm to an isolated diagnostic destination: 518 rows validated in about 4.3 seconds. Its trace records one index construction. The algorithm, supplied data, historical extraction caches and root output.csv were not changed by this investigation. The evaluation helper is never imported by the production CLI, and restores the temporary workflow function after success or failure.

**250 default-profile tests pass**, including three new independent evaluation-safety tests: reject altered predictions before reference access, reject source-snapshot path traversal, and restore production assignment after failed controls while constructing the index once. The existing assignment-boundary tests remain in place. No expected resource association was inserted into prediction logic.

## Additional evidence search

A separate metadata pass inspected 43 manifest artifacts: decoded JSON keys and values; PNG text/EXIF metadata; PDF metadata, form fields, annotations and embedded attachments. It found **0 target hits and 0 inspection errors** for the two security IDs and two account IDs. Source IDs, capture times and content hashes are retained in the diagnostic JSON. This supplements the prior SQL, log, historical-identifier, unresolved-reference and rendered-media investigation; it does not turn a failed search into deletion proof.

No additional subject-bearing relationship was found for audit_record_6645 or audit_record_5569, or to distinguish ownership of account_410 and account_7015. Numeric identifiers, request dates and event order do not supply those missing relationships. A future supported correction would need such evidence; this iteration does not claim that no possible future approach could improve the score.

## Reproduce

Use new output paths for every freeze:

```powershell
python -B code/evaluation/assignment_experiment.py predict --run runs/accuracy-repeat --repeats 3
python -B code/evaluation/assignment_experiment.py compare --run runs/accuracy-repeat
python -B code/evaluation/inspect_embedded_evidence.py --target audit_record_6645 --target audit_record_5569 --target account_410 --target account_7015 --out runs/embedded-repeat.json
python -B code/main.py --no-llm --out runs/production-repeat.csv --trace runs/production-repeat-trace.json
python -m pytest code/benchmark_tests -q
```

Production target SHA-256 remains `e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc`. Combined baseline prediction SHA-256 remains `10a0adaba9d7837037ff41f7553e01a2f38e0b3243c62072efe2c69894ba061f`. Candidate CSVs, source snapshots, repeated timings, complete comparison JSON and metadata inspection outputs are isolated under runs/accuracy-search/; they do not replace the submission. Other pre-existing working-tree edits were preserved.
