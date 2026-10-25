# Measured public-sample iteration — 25 October 2026

Final status accuracy is **6/32 (18.75%)**; full-case exact accuracy is **1/32 (3.12%)**. Prediction coverage is 6/32; the other 26 executions remain explicit failures and count as incorrect in both accuracy denominators. This is an incomplete solution, not a submission-ready result. The interim 11/32 status result fell after removing unsupported policy/coverage assumptions; that regression is retained in this report.

## Evaluation protocol

`sample_eval.py predict` runs the same input, extraction, shared-index, investigation, compilation and validation tools as the real coordinator. It continues after per-case failures so all 32 requests can be diagnosed. It never opens the public reference file. The normal production coordinator still stops on failure and publishes only after every request validates. A diagnostic partial CSV cannot be submitted as the final output.

Each run uses a new directory and seals prediction/failure/request hashes, production-source snapshots, source hashes and case membership before `compare` opens public answers. New runs also check source bytes before and after prediction, and seal a text-free resource/state/source reasoning trace. Earlier snapshots were taken immediately after prediction; no production source was edited during those runs. Comparisons reject altered predictions, failures, snapshots or reasoning traces. These are integrity checks, not cryptographic authentication against rewriting the entire manifest. No hidden truth or generator inputs were used, and the supplied dataset was not changed.

Earlier conversation work inspected public examples. **This is not a blind evaluation.** The separation prevents each run from consuming reference answers; it cannot undo earlier human/assistant knowledge. Fixes are general schema/intent rules and tests use independent synthetic subjects, resources and traces. Prediction modules contain no public case-number rules, answer imports, numeric suffix joins or case-specific corrections.

## Measured runs

| Run | Coverage | Status correct / 32 | Full case exact / 32 | Largest failure category and response |
|---|---:|---:|---:|---|
| 00, original pipeline | 0 | 0 (0%) | 0 (0%) | Unsupported extraction, 32 cases: implement native format adapters first. |
| 01, native format coverage | 3 | 3 (9.38%) | 0 (0%) | 27 unresolved investigations; fixed-code diagnostics reveal request intent in 26. |
| 01 diagnostic refactor | 3 | 3 (9.38%) | 0 (0%) | Same CSV bytes and failure stage/type outcomes; only root diagnostics added. |
| 02, explicit intent grammar | 11 | 11 (34.38%) | 1 (3.12%) | Remaining intent 10, policy 7, ownership 2, state 2. |
| 03, policy/coverage safeguards | 6 | 6 (18.75%) | 1 (3.12%) | Reject invented witnesses and unrepresented media; five status-correct candidates withdrawn. |
| Final, independent validation and telemetry repair | 6 | 6 (18.75%) | 1 (3.12%) | Same CSV bytes and failure outcomes as run 03. |

Every changed prediction is explained in [prediction_changes.md](prediction_changes.md). Full case-by-case missing/extra steps and all field/order deltas are in [sample_final.md](sample_final.md), with historical [run 00](sample_iteration_00.md), [run 01](sample_iteration_01.md), [run 02](sample_iteration_02.md), and [run 03](sample_iteration_03.md) reports. The comparator includes resource, system, phase, operation, state, evidence ID, numbering and array order. Unmatched steps remain visible rather than being forced into a guessed correspondence.

## Metric definitions and final counts

| Metric | Final result | Definition |
|---|---:|---|
| Status accuracy | 6/32 = 18.75% | Exact status; failed executions are incorrect. |
| Full-case exact accuracy | 1/32 = 3.12% | Correct status and entire ordered seven-field step array. JSON object key order is ignored. |
| Exact sequence accuracy | 1/32 = 3.12% | Entire step array; a failed execution is never an exact empty sequence. |
| Exact-step precision | 17/23 = 73.91% | All seven fields agree, including numbering and citation; denominator is produced steps. |
| Exact-step recall | 17/193 = 8.81% | Same exact step criterion; denominator includes every reference step in all 32 cases. |
| Field accuracy | 155/1,351 = 11.47% | Seven fields per reference step; diagnostic semantic alignment; missing steps contribute zero correct fields. Extra steps are reported separately and affect precision. |

Among the six produced cases, status accuracy is 6/6 and full exact is 1/6. Those conditional figures are not the headline result. Across their step arrays there are eight missing steps, no extra steps, six numbering-field errors and no detected relative-order error. Across all 32 cases, 170 reference steps are missing. No observed resource/operation/state/citation field mismatch in the surviving rows proves general correctness: ownership and cutoff exclusions prevent many expected rows from being produced at all.

## Root causes, evidence and decisions

The initial largest category was extraction unsupported (32). Deterministic adapters now parse the supplied JSON families, native service traces, table-scoped SQL snapshots, PDF text and local Windows OCR. SQL executes only in memory with a restricted authorizer and instruction bound. OCR never calls a hosted model. This removes the format-level failure but does not prove semantic completeness.

The next largest measured category was intent (26). The old grammar rejected courtesy conditions, explicit prior-deletion reviews, full-account imperatives and supported non-English deletion wording. General clause-scoped rules now accept explicit deletion/audit requests while preserving unknown, partial, quoted and conditional scope for optional intent review. Ten sample requests still fail deterministic intent parsing; no blanket deletion default or sample-specific wording table was added.

Final execution failures are: intent 10; policy proof 9; relevant unrepresented media 4; missing ownership 2; missing state 1. These are first-blocker counts, not an assertion that each case has only one defect. Deeper diagnoses identify the following policy failures:

| Cases | Source evidence | Missing proof |
|---|---|---|
| 11, 13, 14 | evidence_03 handover: lines 40, 34, 41 | Security retention expiry is absent. Additional support/attachment/restore conditions are also missing at lines 46, 43, 19 respectively. |
| 16, 22 | evidence_05 primary and read-replica tables | Security records have no retention expiry in the selected copies. Presence alone does not prove the retention condition. |
| 18 | evidence_94, line 11 | Support readback has identity fields but no shared-context witness. |
| 28, 30 | evidence_92, ticket rows 0 and 4 | A delivery-query excerpt does not satisfy the current conservative shared/order/agent predicate. This may reject valid retained context and needs a reviewed general interpretation. |
| 32 | evidence_51, /snapshots/2/records/1 | Retained security record lacks a retention expiry. |

The five surviving non-exact predictions have eight missing checks:

| Case | Missing expected checks | Evidence reasoning concern |
|---|---|---|
| 03 | Anonymized analytics_9406 | Its readback contains cleared identifiers; a state read is not a subject ownership link. Do not assign it by numbering. |
| 06 | Absent account_006 | Need a literal subject/resource link plus a scoped absence witness; do not synthesize this resource from case or user suffixes. |
| 09 | Absent account_3960; retained audit_record_4902 | Relevant service log is captured on September 18, after the September 16 audit, despite earlier row times. The conservative capture/availability gate excludes it. |
| 20 | Absent account_5037; retained audit_record_5569 | Ownership/cutoff discovery does not supply these checks; preserve the gaps rather than importing reference resource lists. |
| 23 | Absent account_410; retained audit_record_4128 | Same unresolved discovery/eligibility issue. No naming-based completion is justified. |

Cases 01 and 04 have no eligible grounded resource ownership under the current rules; case 07 selects a resource with no eligible state witness. Four media gaps block cases 15, 17, 21 and 24. The parser found unrepresented subject identifiers in two PDFs and five screenshots overall; a gap affects only an eligible matching subject, while a blank unscoped document blocks all relevant audits. This is conservative and incomplete, not a claim that OCR found all PII.

## Regression checks and remaining uncertainty

All **103 tests pass**: 31 coordinator, 17 explicit-evidence, 37 model/cache and 18 new iteration regressions. The new cases cover reference isolation, all-32 denominators, immutable runs, source tampering, byte-preservation enforcement, mandatory explanations, field/order/resource/operation differences, courtesy and deletion conditions, prior-deletion audit intent, multilingual/negated scope, SQL copy/table boundaries and denied side effects, log trace ownership, missing versus null fields, absence versus selectors, row-local OCR ownership and subject-scoped coverage gates. Existing fake-client tests still verify malformed responses, corrupt caches and budget exhaustion. The independent three-case fixture remains byte-identical at SHA-256 `7f9d5079d7299856e9c7ea89de1c9721bbe8148da35955c1451a42d3a010e315`.

The first full-suite check after adding a new `evidence_gaps` count failed because the telemetry allowlist had not been extended. That integration defect was fixed, then the entire suite passed. It did not change sample prediction bytes. The evaluator also received a regression ensuring that a failed prediction with an expected empty array cannot earn sequence credit.

Remaining correctness work includes media layout coverage, explicit partial-scope intent, trustworthy ownership after identifiers are cleared, complete table-scoped negative queries, physical-copy inventory, retention/condition provenance across observations, and a reviewed rule for enclosing capture times versus retrospective observations. The inherited continuity mutation list and single-citation aggregation limitations remain. No rule was weakened just to match a reference answer, and no historical extraction cache or prompt provenance was relabeled.

No root output.csv has been produced; no completed 518-row accuracy or submission readiness is claimed. Sample runs made zero hosted inference calls and used no provider credentials. HackerRank / InterviewStreet attribution in the repository and supplied materials is preserved. These public samples do not measure hidden accuracy or certify real-world deletion.
