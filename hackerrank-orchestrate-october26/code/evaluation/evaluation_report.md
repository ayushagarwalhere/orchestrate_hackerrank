# Current verification in orchestrate_hackerrank

The intended folder now reproduces **32/32 public statuses and 29/32 full-case exact predictions** using the same authorized approach requested by the user. The actual default CLI validates and publishes all 518 rows. Its CSV is byte-identical to the previous high-scoring profile (SHA-256 e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc): zero changed predictions across all 518 requests.

Fresh integration checks: **247 default-profile tests pass in 61.65 seconds; all 124 independent-profile tests pass in 42.861 seconds**. An earlier independent timing test exceeded its wall-clock threshold during host contention; the final full suite passed with the threshold unchanged. The CLI trace records exactly one index construction. There were no new hosted inference calls.

Status accuracy and full-case exact accuracy are separate. The same three exact mismatches remain; no hidden-score improvement, supported ownership for the ambiguous account, or missing security association is claimed. [repository_migration.md](repository_migration.md) explains the profile choice, original attribution, executable entry points, output hashes and inherited assumptions. The independent coordinator remains available as proof_main.py; its partial diagnostic runs must not be confused with the default output.

## Historical evaluation record transferred with the authorized profile

The following is the previous checkout's report, preserved as historical context. Its old test counts and archive paths are not new measurements in this repository.

# Local evaluation — authorized derivative

Adapted with author permission from rsrsp21 commit 0c573f824adb5b4c0aef36a525d5dc424dc9f97d. Original design/tests/extraction are credited in UPSTREAM.md; local work is in CHANGES.md. The user confirms the unchanged baseline earned 28.2/30. The modified candidate has not been graded; no higher score is claimed.

Produced 518 rows with statuses {'INCOMPLETE': 354, 'COMPLETE': 154, 'NOT_APPLICABLE': 10}. Output SHA-256: `e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc`. Generation and local evaluation took 4.211s; zero live model calls.

## Public sample evaluation

All predictions precede reference access. Whole-array equality includes step numbers, operations, IDs, states, evidence and order. Status accuracy is separate.

```text
=== public samples: 32 cases
status accuracy   1.0000
step precision    0.9948  recall 0.9845  F1 0.9896  (191 predicted / 193 expected)
sequence exact    0.9062
field accuracy    step_no=0.9896  phase=0.9896  system_id=0.9689  resource_id=0.9637  operation=0.9689  state=0.9689  evidence_id=0.9896
  case_18: status INCOMPLETE (expected INCOMPLETE)
      - missing ('VERIFICATION', 'security_service', 'audit_record_6645', 'VERIFY_RECORD_PRESENT', 'PRESENT', '')
  case_20: status INCOMPLETE (expected INCOMPLETE)
      - missing ('VERIFICATION', 'security_service', 'audit_record_5569', 'VERIFY_RECORD_PRESENT', 'PRESENT', '')
  case_23: status INCOMPLETE (expected INCOMPLETE)
      - missing ('VERIFICATION', 'account_service', 'account_410', 'VERIFY_RECORD_ABSENT', 'ABSENT', '')
      + extra   ('VERIFICATION', 'account_service', 'account_7015', 'VERIFY_RECORD_ABSENT', 'ABSENT', '')
```

## All 32 sample cases

| Case | Expected status | Predicted status | Expected steps | Predicted steps | Full case exact | Missing | Extra |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: |
| case_01 | COMPLETE | COMPLETE | 1 | 1 | yes | 0 | 0 |
| case_02 | COMPLETE | COMPLETE | 1 | 1 | yes | 0 | 0 |
| case_03 | COMPLETE | COMPLETE | 3 | 3 | yes | 0 | 0 |
| case_04 | COMPLETE | COMPLETE | 2 | 2 | yes | 0 | 0 |
| case_05 | INCOMPLETE | INCOMPLETE | 3 | 3 | yes | 0 | 0 |
| case_06 | INCOMPLETE | INCOMPLETE | 4 | 4 | yes | 0 | 0 |
| case_07 | INCOMPLETE | INCOMPLETE | 4 | 4 | yes | 0 | 0 |
| case_08 | INCOMPLETE | INCOMPLETE | 4 | 4 | yes | 0 | 0 |
| case_09 | INCOMPLETE | INCOMPLETE | 5 | 5 | yes | 0 | 0 |
| case_10 | INCOMPLETE | INCOMPLETE | 4 | 4 | yes | 0 | 0 |
| case_11 | INCOMPLETE | INCOMPLETE | 14 | 14 | yes | 0 | 0 |
| case_12 | INCOMPLETE | INCOMPLETE | 5 | 5 | yes | 0 | 0 |
| case_13 | INCOMPLETE | INCOMPLETE | 8 | 8 | yes | 0 | 0 |
| case_14 | INCOMPLETE | INCOMPLETE | 5 | 5 | yes | 0 | 0 |
| case_15 | INCOMPLETE | INCOMPLETE | 5 | 5 | yes | 0 | 0 |
| case_16 | INCOMPLETE | INCOMPLETE | 7 | 7 | yes | 0 | 0 |
| case_17 | INCOMPLETE | INCOMPLETE | 5 | 5 | yes | 0 | 0 |
| case_18 | INCOMPLETE | INCOMPLETE | 14 | 13 | no | 1 | 0 |
| case_19 | INCOMPLETE | INCOMPLETE | 8 | 8 | yes | 0 | 0 |
| case_20 | INCOMPLETE | INCOMPLETE | 8 | 7 | no | 1 | 0 |
| case_21 | COMPLETE | COMPLETE | 3 | 3 | yes | 0 | 0 |
| case_22 | INCOMPLETE | INCOMPLETE | 8 | 8 | yes | 0 | 0 |
| case_23 | INCOMPLETE | INCOMPLETE | 8 | 8 | no | 1 | 1 |
| case_24 | INCOMPLETE | INCOMPLETE | 7 | 7 | yes | 0 | 0 |
| case_25 | COMPLETE | COMPLETE | 3 | 3 | yes | 0 | 0 |
| case_26 | COMPLETE | COMPLETE | 6 | 6 | yes | 0 | 0 |
| case_27 | COMPLETE | COMPLETE | 6 | 6 | yes | 0 | 0 |
| case_28 | COMPLETE | COMPLETE | 6 | 6 | yes | 0 | 0 |
| case_29 | INCOMPLETE | INCOMPLETE | 14 | 14 | yes | 0 | 0 |
| case_30 | INCOMPLETE | INCOMPLETE | 14 | 14 | yes | 0 | 0 |
| case_31 | COMPLETE | COMPLETE | 3 | 3 | yes | 0 | 0 |
| case_32 | INCOMPLETE | INCOMPLETE | 5 | 5 | yes | 0 | 0 |

The baseline and candidate both have 32/32 correct statuses and 29/32 exact sequences; the baseline output was independently reproduced byte-for-byte with SHA-256 `0d80a7d4bad671870762bf5a6edab41a9c48d146dd2292367e5cb8b228207194`.

## Measured candidate differences

Only three target-case evidence fields change. No status, resource ID, operation, state or array order changes. Each previously blank COMPLETE account verification now uses the most recent eligible prior absence under the inherited coverage model, provided no newer presence or creating operation invalidates it. This is a general rule, not a case-ID correction. Pre-request persistence and authoritative scope are assumptions that must remain visible, not a hidden-score guarantee.

| Case | Resource | Before | Candidate |
| --- | --- | --- | --- |
| case_45 | account_003 | (empty) | evidence_54 |
| case_126 | account_8819 | (empty) | evidence_15 |
| case_127 | account_6805 | (empty) | evidence_15 |

## Additional cases and tests

Recorded final test run: **175 passed in 30.16 seconds**. The command and environment are recorded in test_run.json. This includes the 152 upstream tests plus local identity, evidence, model-boundary, SQL and coordinator regressions. Tests ran separately; rerunning this report alone does not rerun pytest.

Local counterexamples cover: two future email changes; an eligible snapshot unaffected by later changes; an already-absent account before its request; later sync invalidation; a newer presence blocking stale absence; impossible post-capture observations; preserving image clocks; international phone normalization; rejecting uncited COMPLETE; and image hash mismatch. The inherited custom-case harness also passes 12/12.

The current agent architecture pass adds typed tool contracts, a real CLI coordinator, aggregate execution traces, validation before atomic publication, bounded model calls, cache-hit validation, new versioned prompts and confined manifest/SQL loading. The CSV remains byte-for-byte identical to the prior three-citation candidate. See ../ARCHITECTURE.md and DECISION_GUIDE.md for design rationale and an explicitly editorial guide to the actual development record. Historical prompts were not rewritten.

## Limitations and inherited behavior

The upstream scoring profile retains timing inference, numeric case-order tie breaks, a naming fallback and retrospective ownership membership. The local identity fix removes intermediate future values but does not turn retrospective metadata into information available earlier. State citations obey their clocks, and impossible post-capture observations are now rejected. Unknown permission defaults and other inherited inference assumptions remain review issues; do not call this a fully strict proof engine.
The validator now rejects empty COMPLETE citations and passes all 518 candidate rows; it does not establish historical ownership or hidden canonical correctness. No sample answer, imported output CSV or per-case lookup table enters prediction logic. Dataset files were not modified.

A focused reinspection found no indexed observations or activity for the two missing audit resources. This is an extraction/inventory diagnostic, not proof that their IDs are absent from every rendered artifact. The account mismatch has two unowned failed delete candidates in the same timing window; the inherited case-order tie break chooses the wrong one. No supported replacement ownership link was established, so no sample-ID correction was introduced. The detailed missing/extra tuples above expose every operation, state, resource and evidence difference; shifted positions arise from these inventory differences, rather than an independent sort defect.

## Subsequent request-interpretation and evidence-ledger iteration

The latest source passes 233 tests (175 prior tests plus 58 new regressions). All 550 frozen request predictions remain byte-identical; sample status accuracy remains 32/32 and full-case exact accuracy remains 29/32. This is a reliability improvement, not a measured public-score increase. The actual CLI now exports a detailed source ledger with --ledger while retaining an aggregate-only trace.

The shared index contains 3,101 observations and 14 declared coverages from all 94 files. Twenty ledger references remain unresolved, separately from 22 unresolved case references and 137 states without a current witness. Empty extraction is not absence; unresolved intent or explicit unknown readbacks stop publication. Historical caches and source attribution are preserved. See [request_ledger_report.md](request_ledger_report.md) for the frozen hashes, failure tests, rendered-source review and remaining inherited assumptions.


## Targeted investigation of the three remaining mismatches

See [three_mismatch_investigation.md](three_mismatch_investigation.md) for exact source locations, clocks, subject identifiers, conflicts, rendered-document review and reproducible searches. The earlier account investigation's two-candidate description was incomplete: account_9155/activity_3663 is a third unowned failed candidate in the same window. None of the three has a subject-bearing ownership witness. Numeric case order and event order explain the current selection but cannot justify swapping to the public reference ID.

Neither audit_record_6645 nor audit_record_5569 was located in participant sources, including all SQL captures, decoded JSON, correlated logs, unresolved ledger references, seven rendered PDF pages and eleven screenshots. No supported general correction was found, and all three mismatches remain unresolved. The added utility is read-only and excluded from prediction; its tests use independent synthetic examples rather than expected associations.

Final validation: **247 tests passed in 45.04 seconds**. All 518 target predictions and the combined 550-row freeze are byte-identical; the actual offline CLI independently produced the same 518-row SHA-256 e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc. Zero changed predictions, no production resolver changes and no hosted inference. Public status accuracy remains 32/32; full-case exact accuracy remains 29/32. Missing-source evidence is not deletion proof or evidence that the public reference is wrong.
