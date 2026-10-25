# Evaluation report — 25 October 2026

The current public-sample result is **6/32 status correct (18.75%)** and **1/32 full-case exact (3.12%)**, with 26 execution failures counted as incorrect. All 32 requests are compared; no failures are omitted from the denominators. The earlier 11/32 status result regressed after removing unsupported policy witnesses and incomplete media coverage. This is an interim engineering result, not a completed challenge submission.

## Public metrics

| Metric | Result |
|---|---:|
| Prediction coverage | 6/32 |
| Status accuracy | 6/32 (18.75%) |
| Full-case exact accuracy | 1/32 (3.12%) |
| Exact ordered arrays | 1/32 (3.12%) |
| Exact seven-field step precision | 17/23 (73.91%) |
| Exact seven-field step recall | 17/193 (8.81%) |
| Field accuracy, missing steps scored zero | 155/1,351 (11.47%) |
| Missing / extra steps across all cases | 170 / 0 |

Field alignment diagnoses errors without changing predictions. Exact step/array metrics include numbering, citations and array order; JSON object-key order is irrelevant. Conditional on the six produced cases, statuses are 6/6 and full cases 1/6, but these are not all-case accuracy.

Predictions were frozen before the separate comparison command opened public answers. Earlier conversation work inspected public examples, so this is **not blind evaluation**. Production code does not import references, expected arrays or case-specific corrections. See [iteration_report.md](iteration_report.md) for root causes, measured iteration, regressions, assumptions and exact metric definitions; [prediction_changes.md](prediction_changes.md) explains every changed prediction. [sample_final.md](sample_final.md) lists full missing/extra steps and resource/evidence/operation/state/number/order differences for every non-exact case.

## All 32 public cases

| Case | Predicted | Reference | Status correct | Full case exact | First failure / deltas |
|---|---|---|---|---|---|
| case_01 | NO PREDICTION | COMPLETE | False | False | investigate:missing_ownership |
| case_02 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_03 | COMPLETE | COMPLETE | True | False | missing=1, extra=0, fields=0, order=False |
| case_04 | NO PREDICTION | COMPLETE | False | False | investigate:missing_ownership |
| case_05 | INCOMPLETE | INCOMPLETE | True | True | missing=0, extra=0, fields=0, order=False |
| case_06 | INCOMPLETE | INCOMPLETE | True | False | missing=1, extra=0, fields=1, order=False |
| case_07 | NO PREDICTION | INCOMPLETE | False | False | investigate:missing_state |
| case_08 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_09 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, fields=1, order=False |
| case_10 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_11 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_12 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_13 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_14 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_15 | NO PREDICTION | INCOMPLETE | False | False | investigate:unrepresented_evidence |
| case_16 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_17 | NO PREDICTION | INCOMPLETE | False | False | investigate:unrepresented_evidence |
| case_18 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_19 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_20 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, fields=2, order=False |
| case_21 | NO PREDICTION | COMPLETE | False | False | investigate:unrepresented_evidence |
| case_22 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_23 | INCOMPLETE | INCOMPLETE | True | False | missing=2, extra=0, fields=2, order=False |
| case_24 | NO PREDICTION | INCOMPLETE | False | False | investigate:unrepresented_evidence |
| case_25 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_26 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_27 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_28 | NO PREDICTION | COMPLETE | False | False | compile_plan:policy_unresolved |
| case_29 | NO PREDICTION | INCOMPLETE | False | False | investigate:request_intent |
| case_30 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |
| case_31 | NO PREDICTION | COMPLETE | False | False | investigate:request_intent |
| case_32 | NO PREDICTION | INCOMPLETE | False | False | compile_plan:policy_unresolved |

## Independent participant-created evaluation cases

These three hand-authored synthetic cases in `tests/test_workflow.py` compare independent expected arrays, not compiler-generated expectations. They include the status absent from the public samples.

| Case | Input evidence and request | Expected result |
|---|---|---|
| A | Explicit deletion; reported complete; profile present; copying flow active; security record in retention | INCOMPLETE; report profile and flow, disable flow before deleting profile, verify absent profile, present security record and disabled flow. |
| B | Explicit deletion; reported not started; eligible lookup says profile absent | COMPLETE; evidence-backed absence check. |
| C | Export request with explicit do-not-delete negation | NOT_APPLICABLE; empty array. |

Fixture status accuracy is 3/3, exact steps 8/8, fields 56/56, and exact arrays 3/3. These test wiring and invariants, not hidden accuracy. CSV SHA-256 remains `7f9d5079d7299856e9c7ea89de1c9721bbe8148da35955c1451a42d3a010e315`.

## Validation and fixes

`python -B code/evaluation/main.py` runs all 103 tests: 31 coordinator, 17 explicit evidence, 37 model/cache and 18 measured-iteration tests. All pass. Tests use synthetic subjects and fake model clients; none makes hosted inference calls. They exercise actual CLI/coordinator wiring, a single reused immutable index, safe publication, telemetry privacy, source/ownership/state separation, historical identifiers, physical/table scope, model budgets/cache provenance and malformed-response failure paths.

The largest initial failure was unsupported extraction (32 cases), addressed with general native adapters. Root diagnostics then exposed intent parsing (26 cases), addressed with clause-scoped explicit deletion/audit grammar. Safeguards removed invented shared-context witnesses, preserve missing fields as unknown, and represent unassigned media identifiers as coverage gaps. Five status-correct predictions were withdrawn rather than represented as successful deletion. The first integration check caught a missing telemetry count allowlist entry; that was fixed and the complete suite passed. See the iteration report for each policy source/locator and remaining work.

The diagnostic refactor preserved prediction bytes and failure outcomes. Subsequent independent gap validation and telemetry repair also preserved the final prediction bytes (`f97f6e6d396271e1e955e874f81c1fd808559892bb348a925922ae3ab4b0b574`). Correctness changes have an explanation for every changed prediction. Full-dataset byte equivalence is unavailable because there is no complete 518-row output before or after these changes.

## Limitations

The six surviving rows still omit eight expected checks across five cases; only case_05 is full-case exact. Remaining failures include intent (10), policy (9), media coverage (4), ownership (2) and state (1). The strict enclosing-capture gate can exclude relevant retrospective observations. SQL negative-query coverage, ownership of cleared records, policy metadata continuity, indirect identifiers, OCR layout interpretation and multi-source citations remain unresolved. A correct status is not evidence that the entire audit or plan is correct.

The earlier full-dataset smoke stopped at unsupported extraction. Current format adapters have been exercised across all 94 supplied artifacts by sample prediction; no new completed full-dataset run or root output.csv is claimed. The production CLI remains all-or-nothing on unresolved investigations. Supplied participant data and upstream attribution are unchanged; organizer-only truth and generator internals were not consulted.
