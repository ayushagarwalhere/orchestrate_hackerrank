# Intended repository: baseline restored

The active project is `hackerrank-orchestrate-october26/` in **ayushagarwalhere/orchestrate_hackerrank**. The original upload stored that directory as a Git link (mode 160000) to the HackerRank starter commit rather than its actual working files. Commit `37a7d01` replaces it with browsable files. The local nested `.git` directory was preserved; it is not uploaded.

## Measured result in this folder

| Check | Result |
|---|---:|
| Public status accuracy | Not reported |
| Public full-case exact accuracy | Not reported |
| Matching semantic steps | 190 of 191 produced / 193 expected |
| Target CSV | 518 validated rows |
| Target statuses | 154 COMPLETE, 354 INCOMPLETE, 10 NOT_APPLICABLE |
| Difference from the previous local target CSV | **Zero bytes; all 518 rows identical** |
| New hosted inference calls | 0 |

The target CSV SHA-256 is `e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc`. The default CLI generated it here, then a separate local evaluation pass froze the target/public predictions. Semantic step matching excludes numbering; full-case exactness includes every step field, numbering and array order. No hosted or hidden accuracy result is claimed.

## What changed

The default CLI uses the preserved local coordinator. Its observations, identifier
history, ownership links, workflow candidates, shared evidence index,
deterministic policy compiler, publication guards, ledger and bounded model/cache
boundaries are transferred together. The coordinator is named
`benchmark_agent.py` to avoid colliding with the preserved independent
`audit_agent` package. This name change does not change its decisions. Historical
cache and prompt provenance remain documented locally; no dataset, old prediction
CSV, credentials or conversation transcript was imported from the other checkout.

All 101 participant inputs were compared byte-for-byte with the previous checkout and are identical. Public references remain outside the prediction pipeline. No expected-answer lookup, sample-ID mapping or expected remediation step was inserted.

The independent conservative implementation remains available through `code/proof_main.py`, its `code/audit_agent/` package, `code/tests/` and `code/evaluation/proof_tests.py`. Its request-interpretation and support-context improvements are retained. Before switching the default, it produced 10/32 correct public statuses and 1/32 exact cases; its target diagnostic covered 234/518 requests, with 284 explicit failures. Those partial results are not a submission and are not the default profile's output.

Changing the default is a deliberate profile selection, **not** a claim that
the conservative implementation was structurally refactored into identical
predictions. All 518 default predictions are instead identical to the earlier
local profile selected for reproduction.

## Assumptions and remaining mismatches

The default profile retains the earlier timing windows, reported-result filtering, numeric case-order tie-breaks, naming fallback, retrospective ownership membership and logical snapshot coverage assumptions. Activity results are not direct state proof; some ownership remains inferred. This explains why it produces a complete CSV where the independent profile stops. Its public result does not establish that those assumptions hold on hidden cases or in real systems.

The same three public mismatches remain: missing retained-security verifications for audit_record_6645 and audit_record_5569, and account_7015 selected where the reference expects account_410. The participant sources did not provide the missing security IDs or a subject-bearing link distinguishing the account candidates. Nothing in this transfer manufactures those relationships. See `three_mismatch_investigation.md` for exact locations, clocks, rendered-source review and reproducible searches.

Earlier transcripts and reports from the successful checkout are historical evidence of that work; their old archive paths and test counts do not assert artifacts or fresh test executions in this repository. The fresh test results for this integration are recorded in the evaluation report.

## Reproduce

```powershell
python -m pip install -r requirements.txt
python -B code/main.py --no-llm --trace runs/default-trace.json --ledger runs/default-ledger.json
python -B code/validate_output.py
python -B code/evaluation/score.py
python -m pytest code/benchmark_tests -q
python -B code/evaluation/proof_tests.py
```

The actual CLI builds its index once and reuses it across all requests. `--trace` records aggregate outcomes and durations; `--ledger` is an explicit detailed source export. New live inference requires `--enable-model`; this reproduction used historical screenshot facts and no new provider calls. Historical extraction cost/provenance is not relabeled as a new zero-cost extraction.
