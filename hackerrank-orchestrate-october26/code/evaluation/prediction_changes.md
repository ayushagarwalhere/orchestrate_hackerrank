# Every changed public-sample prediction

These are evaluation explanations. No reference rows or case-specific corrections are imported by prediction modules. Failure-to-failure diagnostic transitions are listed separately in the iteration report. Full old/new arrays and field deltas remain sealed locally under `runs/*_changes.json`; the explanations below are included in the submission-visible Markdown.

## sample_iteration_00 → sample_iteration_01

| Case | Change | Evidence-supported explanation |
|---|---|---|
| case_09 | execution failure → INCOMPLETE | Reviewed native JSON, log, SQL, PDF and local OCR adapters replace the global unsupported-extraction failure; the unchanged deterministic investigator/compiler can now emit the source-backed subset. |
| case_18 | execution failure → INCOMPLETE | Reviewed native JSON, log, SQL, PDF and local OCR adapters replace the global unsupported-extraction failure; the unchanged deterministic investigator/compiler can now emit the source-backed subset. |
| case_20 | execution failure → INCOMPLETE | Reviewed native JSON, log, SQL, PDF and local OCR adapters replace the global unsupported-extraction failure; the unchanged deterministic investigator/compiler can now emit the source-backed subset. |

All other prediction rows are unchanged.

## sample_iteration_01_refactor → sample_iteration_02

| Case | Change | Evidence-supported explanation |
|---|---|---|
| case_03 | execution failure → COMPLETE | The generic full-account French deletion grammar now recognizes an explicit suppression request. Evidence and policy decisions are unchanged. |
| case_05 | execution failure → INCOMPLETE | Explicit earlier deletion plus a request to remove remaining copies now authorizes an offline audit. The existing eligible profile readback drives the plan. |
| case_06 | execution failure → INCOMPLETE | An account-page-gone statement plus a removal request is recognized as a retrospective deletion audit; existing search readbacks drive remediation. |
| case_21 | execution failure → COMPLETE | Explicit earlier account deletion plus a verification request now authorizes audit; retained-state reconstruction is unchanged. |
| case_23 | execution failure → INCOMPLETE | A policy-retention condition in a separate clause no longer makes the unconditional full-account deletion request conditional. |
| case_24 | execution failure → INCOMPLETE | A prior-complete deletion claim plus an explicit investigate-and-finish request now authorizes audit, without treating the claim as state proof. |
| case_28 | execution failure → COMPLETE | A request to verify prior account deletion is recognized; a separate instruction excluding a near-match is not mistaken for a deletion negation. Identity matching remains exact. |
| case_30 | execution failure → INCOMPLETE | A prior-deleted account statement plus a request to handle residual traces now authorizes audit; existing evidence still determines current state. |

All other prediction rows are unchanged.

## sample_iteration_02 → sample_iteration_03

| Case | Change | Evidence-supported explanation |
|---|---|---|
| case_18 | INCOMPLETE → execution failure | Withdrawn: support readbacks no longer acquire an invented shared-context witness. Missing policy proof causes policy_unresolved. |
| case_21 | COMPLETE → execution failure | Withdrawn: relevant media has visible subject identifiers that cannot all be assigned to a grounded resource. A subject-scoped coverage gap now blocks the incomplete conclusion. |
| case_24 | INCOMPLETE → execution failure | Withdrawn: relevant media has unrepresented subject evidence; the previous nonempty plan did not establish complete evidence coverage. |
| case_28 | COMPLETE → execution failure | Withdrawn: support records no longer acquire synthetic retained-conversation witnesses; missing policy proof is unresolved. |
| case_30 | INCOMPLETE → execution failure | Withdrawn: the former any-message-text rule is narrowed to actual shared/order/agent context. The delivery-query excerpt at evidence_92, /service_exports/support_platform/tickets/4, does not satisfy that conservative predicate; the compiler now reports missing policy proof. This may be overly restrictive. |

All other prediction rows are unchanged.

## Architectural changes

The diagnostic-reason refactor (`sample_iteration_01` → `sample_iteration_01_refactor`) preserved prediction CSV bytes and all failure stage/type outcomes. SHA-256: `3e751f90d9a1de64e9e46ca4208dfd0ff63776e0ac302abf3eb95f9d9fa8d8ef`.

Independent gap validation (`sample_iteration_03` → `sample_iteration_03_validation`) and the telemetry-count allowlist repair (`sample_iteration_03_validation` → `sample_final`) also preserved prediction bytes and failure stage/type outcomes. SHA-256: `f97f6e6d396271e1e955e874f81c1fd808559892bb348a925922ae3ab4b0b574`.

The independent three-case fixture still has CSV SHA-256 `7f9d5079d7299856e9c7ea89de1c9721bbe8148da35955c1451a42d3a010e315`, covering COMPLETE, INCOMPLETE and NOT_APPLICABLE. Full 518-request byte equivalence is unavailable because neither the earlier nor current implementation produces a complete output.
