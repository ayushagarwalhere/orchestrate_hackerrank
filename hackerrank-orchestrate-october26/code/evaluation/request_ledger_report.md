# Request interpretation and evidence ledger — 25 October 2026

Implemented in the published checkout at `Desktop/hacker-rank/hackerrank-orchestrate-october26`, preserving its authorized upstream attribution. The original behavior was frozen before editing. The change adds reliability checks and source accounting; it does not claim a higher public or hidden score.

## Measured verification

| Check | Result |
|---|---|
| Existing tests before changes | 175 passed |
| Final suite | **233 passed**, including 58 new independent regressions |
| Frozen requests | 550: 518 target requests plus 32 public requests used by the inherited joint assignment |
| Prediction preservation | All 550 CSV rows are byte-identical to the frozen baseline |
| Public status accuracy | **32/32 (100%)**, unchanged |
| Public full-case exact accuracy | **29/32 (90.625%)**, unchanged |
| Public exact semantic steps | 190 matches; 191 produced, 193 expected |
| Actual CLI output | 518 validated rows; 154 COMPLETE, 354 INCOMPLETE, 10 NOT_APPLICABLE |
| Hosted inference | No calls, credentials, provider tokens or charges in these verification runs |

The 550-row frozen CSV SHA-256 is `10a0adaba9d7837037ff41f7553e01a2f38e0b3243c62072efe2c69894ba061f`. The 518-row CLI CSV SHA-256 is `e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc`. Predictions were produced before the evaluation pass opened public answers. Earlier work knew public examples, so this is not blind evaluation. No answer rows or case-specific corrections enter prediction logic.

The actual CLI was run with `--no-llm`, `--trace`, and the new `--ledger` option to a diagnostic destination. Exactly one index construction and one ledger export were recorded. Root predictions, supplied data and historical extraction caches were preserved. Existing/concurrent submission artifacts and transcript changes were not reverted. This source iteration does not rebuild historical submission ZIPs or claim they contain the new implementation.

## Request interpretation

Reliable deterministic rules distinguish deletion, access, correction, export-only, marketing opt-out, restoration and questions. General deletion mentions, quoted examples and accidental deletion followed by restoration do not grant deletion authorization. Retention permission is a separate field: legally required records, anonymous statistics and stable references can coexist with deletion. Negation and conditions are scoped to the action they qualify. Conflicts, unsupported wording and conditional deletion remain UNSURE.

Only genuinely ambiguous messages reach the new `intent_fallback/v3` prompt. It encodes the original message as untrusted JSON and has a closed schema for request type, label, supporting character offsets, negation, conditions and retention permission. Live and cached responses use the same validator. Missing cache, malformed response, exhausted budget, provider failure and parser failure remain distinguishable uncertain outcomes. An unresolved authorization stops publication rather than becoming NOT_APPLICABLE. Older prompt/cache provenance is not relabeled or overwritten by the new prompt.

The new tests include independent retention/negation traps, general questions about deletion, correction by replacing a field, export of deleted records, marketing-only scope, restoration, mixed requests, fabricated span offsets, invalid output fields, cache corruption, provider exceptions and budget exhaustion. They test boundaries rather than asserting general natural-language accuracy from a small fixture.

## Ledger and extraction results

All six source families feed the same observations: SQL, JSON, handover text, service logs, PDF pages and screenshots. Observations retain source/resource/system/category/state, identifying-field presence/value, both clocks and exact table/row, JSON pointer, line, page or screenshot-record locations. Selectors remain link keys rather than being mistaken for stored PII. Source hashes and extraction outcomes are recorded separately.

| Corpus measurement | Result |
|---|---:|
| Manifest files / processed files | 94 / 94 |
| Observations / declared snapshot coverages | 3,101 / 14 |
| Extraction failures / missing extraction / required review | 0 / 0 / 0 in the supplied corpus |
| Empty resource extractions | 2: legal-register PDF and SQL inventory; neither creates absence by itself |
| Observed systems | 12; this is not exhaustive physical-system coverage |
| Unresolved ledger references | 20: 9 visual labels, 7 external document references, 3 resource references, 1 unclassified document reference |

The two screenshots with unbound labels and the rendered multi-page support document/register were inspected. A catalog user label previously masked unresolved register rows even though no resource observation was produced. The ledger now records those literal order/user references without assigning invented legal-hold IDs. This has an independent synthetic regression. Page-level identity fields and unknown fields remain inspectable.

Empty parser output is not a negative database query. Unsupported formats, missing files/facts, malformed records and blank/weak unreviewed media have separate extraction outcomes and block publication. Actual negative reads and explicitly declared snapshot scopes remain separate evidence. Missing permission/identifier fields are UNKNOWN, not automatically disabled, blocked, redacted or anonymous. Failed-run tests confirm that the prior CSV remains intact and a requested ledger is refreshed with current failures. Aggregate traces exclude customer text and source identifiers; the explicit detailed ledger can contain source data.

## Remaining uncertainty

The three public mismatches remain: two missing retained-security checks and an account ownership/assignment mismatch. This change does not repair inherited workflow timing, numeric case-order tie breaks, naming fallback, retrospective ownership or physical-copy reduction. Those remain assumptions, not direct evidence.

The coordinator now also exposes 22 unresolved case references and 137 resource states without a current witness. They are separate from confirmed findings. The inherited scoring profile can propose future verification for an INCOMPLETE case without a current account witness; that is not a successful absence check. Non-account candidates without eligible state evidence remain unresolved candidates rather than new findings. A COMPLETE account with unknown state, a selected explicit UNKNOWN readback, or unresolved authorization cannot be published through the new guards.

Historical v2 screenshot facts retain their original provenance; when they lack an original source hash, recording today's artifact hash does not authenticate how those older facts were created. Visual inspection and schema validation do not establish universal extraction completeness or resistance to every prompt injection. The 20 reference issues and broader ownership assumptions still require investigation; the ledger makes them visible instead of claiming they are solved.
