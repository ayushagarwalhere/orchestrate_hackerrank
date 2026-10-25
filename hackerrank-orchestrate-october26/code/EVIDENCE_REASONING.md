> This document describes the preserved independent profile (`code/proof_main.py`, package `audit_agent`). The default CLI is documented in ARCHITECTURE.md and README.md.

# Explicit evidence reasoning and refactor limits

Implemented 25 October 2026. The original HackerRank / InterviewStreet source attribution in [ARCHITECTURE.md](ARCHITECTURE.md) remains applicable. No supplied dataset or policy was edited.

## Separate evidence roles

| Type | Contains | Cannot establish alone |
| --- | --- | --- |
| `Observation` | Source ID (`evidence_id`, also exposed as `source_id`), locator, system/resource, category, interpreted state, capture/observation/availability times, physical copy and query scope, raw field-presence facts, permission facts | Subject ownership; there is no `subjects` field. |
| `OwnershipLink` | Source/locator, resource key, typed identifier, capture/observation/availability times, explicit-reference or catalog-reference basis | Current state, absence, redaction, anonymity or disabled access; there is no state field. |
| `InferenceCandidate` | Proposed association/state, supporting locators, inference kind and named assumptions | A direct readback or a citable state witness. Candidates are never promoted automatically to observations or ownership edges. |

These frozen types live in `audit_agent/evidence.py` and are used throughout the executable extraction, indexing, investigation, validation and telemetry path. `EvidenceBundle`, `ArtifactExtraction` and `ExtractedEvidence` keep them in different tuples. `Investigation` retains its selected state observations, identity links, ownership links, inference candidates and assumptions separately; no new fields are added to the challenge CSV.

Native adapters interpret the supported summary `result` into an observation and `subject_reference` into a separate ownership link. Both can come from one source row without having the same reasoning role. State-only rows can omit ownership. Catalog events can supply ownership without supplying state. Unknown reference conventions produce candidates, not unique ownership claims.

The shared index has `by_identifier` over ownership links, and `by_resource`/`by_source` over observations. Investigation selects resources using eligible ownership, then examines every eligible physical/scope partition of those resources. Source-backed downstream edges can extend the investigation with an explicit association candidate. Arbitrary extractor candidates do not select resources or replace state observations.

Validation independently checks that ownership links are indexed, match the resolved subject and meet the cutoff. State citations must support actual indexed observations, and selected resources must have ownership or a grounded dependency path. The source establishing ownership can differ from the source cited for current state. Ownership-only catalog evidence cannot prove absence.

## Consistent identifiers, including phone prefixes

`audit_agent/identity.py` uses one resolver for current snapshot values and eligible old/new history. Each identifier retains its kind and original raw string. Names are preserved in the trace but are not treated as unique ownership. Email, phone, hash and stable-user keys are typed so identical strings of different kinds do not collide.

Phone normalization removes formatting whitespace, ASCII hyphens, parentheses and dots. It preserves `+`, country-code digits, leading/trunk zeroes and the original raw value. `+44 (20) 1234-5678` matches `+44 20 1234 5678`; neither matches `+1 20 1234 5678` or local `20 1234 5678`. There is no suffix matching, default-country inference, `00`-to-`+` conversion, extension interpretation or transliteration. Other dialing conventions remain unresolved rather than guessed.

Current and historical phones pass through the same function. Old aliases remain discoverable after updates. Future identity rows and ownership links remain ineligible. Historical values become available at the supplied event time, not an invented earlier date. A new value is not itself proof that older copies were updated.

## Physical copies and database scope

Reconstruction partitions a logical resource by `(copy_id, scope.kind, scope.table)`. Latest compatible observations are selected independently per partition. A newer absent primary/table read cannot overwrite a present replica/table read. All selected partitions reach the existing obligation aggregator; the CSV remains a logical projection with physical scope retained in its proof.

`EvidenceScope` distinguishes resource lookups from database queries. A database query names its table and `covered_tables`. An `ABSENT` database observation is invalid unless its table is explicitly included in that coverage. A negative result says nothing about another table, replica, omitted partition or store. Literal table names are retained rather than inferred from resource prefixes.

Native JSON summaries can carry `scope={kind,table,covered_tables}`; reviewed optional adapters emit the same typed scope. Extraction validation and state reconstruction consume it. Tests demonstrate that an absent `profiles` query and a present `archive` query coexist even with the same logical resource and copy label.

This refactor adds no SQL executor or complete SQL snapshot adapter. The supplied `.sql` files still require a reviewed adapter. The scope check validates declared coverage, not whether an external adapter executed a particular query or inspected all tables. Tenant predicates, filters and a complete physical-copy inventory are not fully modeled. These are unresolved correctness concerns, not permission to extrapolate negatives.

## Unknowns stay explicit

`FieldFact` distinguishes `MISSING`, explicit `NULL`, and `VALUE`. Native adapters preserve these states for recognized fields, including result, subject reference, copy/scope, conditions, retention, `enabled` and `restore_allowed`. Unknown extra fields still require a richer adapter instead of being discarded.

`PermissionFact` distinguishes `ALLOWED`, `DENIED`, and `UNKNOWN`. Only explicit booleans map to allowed/denied. Missing and null permissions remain unknown; `bool(None)` is never used. Missing/null/unrecognized result labels become `State.UNKNOWN` in the store; an authorized investigation with an unresolved latest state cannot publish. Source/resource/timestamp essentials are still mandatory.

The current policy projection continues to use interpreted summary states to preserve compatible behavior. It does not yet reconcile every stored field or permission with a state label. Thus a summary saying `BLOCKED` with unknown explicit restore permission still relies on the inherited summary-readback interpretation. The permission remains unknown in the evidence model; this refactor does not silently claim it was observed as denied.

## Assumptions are separate from direct evidence

Assumptions carry a fixed code, source locator and optional resource key. They are not folded into source readings, timestamps or CSV evidence IDs. Telemetry exposes only counts of links, candidates and assumptions, never their customer content.

| Code | Assumption / limit |
| --- | --- |
| `snapshot_update_availability` | Snapshot `updated_at` acts as availability; independent snapshot ingestion time is absent. |
| `csv_event_availability` | History/activity event time acts as availability because ingestion/capture time is absent. A catalog link's capture boundary is explicitly this assumption. |
| `reference_naming` | Email shape, `user_` references, 64-character hex hashes and phone shapes identify kinds. The naming convention is not unique-person proof by itself. |
| `logical_copy_scope` | Missing physical metadata retains the previous `logical` grouping. This does not prove that separate sources observed the same physical copy. |
| `summary_readback` | Supported explicit summary labels retain their previous readback interpretation. Workflow claims may need stronger corroboration. |
| `resource_lookup_coverage` | A summary lookup has declared resource scope when database scope is absent; no claim of every table/store is made. |
| `state_carry_forward` | A reading before `audit_at` is carried to the cutoff under the inherited no-contrary-mutation rule. This is not continuous surveillance. |
| `retrospective_resource_link` | A later but cutoff-eligible ownership link associates an earlier state read with a resource. This assumes no intervening reassignment. |

Investigation generates carry-forward and retrospective candidates with their supporting sources. These expose the continuity and cross-time assumptions used by the inherited reducer; they do not rewrite an observation's time. An extractor candidate proposing absence cannot suppress a concrete present record. A link available after cutoff cannot introduce an earlier reading into the case.

Assumptions and candidates are cutoff-filtered as well as observations and links. Supporting locators use indexed availability boundaries. An unknown locator uses conservative latest-source availability; future metadata cannot enter an earlier case trace merely because it mentions an already-known resource.

## Behavior preservation and verification

All 31 previous coordinator tests continue to pass, including expected failure types. The pre-refactor three-case fixture CSV had SHA-256 `7f9d5079d7299856e9c7ea89de1c9721bbe8148da35955c1451a42d3a010e315`. The refactored CSV is byte-for-byte identical; a permanent regression test asserts this digest as well as the independently authored expected arrays. This covers complete, incomplete and non-deletion fixture paths.

Seventeen added tests cover separate ownership/state sources, ownership without state, state without ownership, candidate non-promotion, required capture time, missing/null/false distinctions, country-preserving historical phones, table-scoped negatives, carry-forward/retrospective assumptions, future ownership/metadata exclusion, preserved names without name-only ownership and validation of owned-resource paths. The complete suite has 48 passing tests.

The real-data smoke result is unchanged: 518 requests and 94 artifacts load, extraction returns `extraction_unsupported`, and no root CSV is published. No complete 518-case output exists before or after this refactor, so full-dataset prediction equivalence cannot be claimed.

Formatting-equivalent phone matching and handling of newly supplied scope/permission metadata are intentional improvements outside the earlier fixture contract. Unknown state is now preserved until investigation rejects it rather than discarded at extraction. These are explicit boundary changes, not a claim that every formerly unsupported input has the same failure behavior.

## Unresolved correctness concerns

1. Summary labels still stand in for actual field-level readbacks. Labels must eventually be reconciled with stored PII, permissions and retention proof. Typed provenance validation does not prove an adapter's semantic or visual interpretation.
2. The compatibility default `logical` can conflate unidentified physical copies. Explicit-copy inventory and stronger coverage should replace that assumption in a separate behavioral change.
3. The inherited continuity rule is incomplete. Its mutation list is not a complete event-history guarantee and omits some events, such as `DELETE_RECORD` when retention could be affected. Resource reassignment, alias reuse and ownership-validity intervals are not fully modeled.
4. Retrospective linking remains an inherited assumption when link time follows observation time but precedes cutoff. It is not contemporaneous ownership proof. Prohibiting or bounding it needs a separate correctness decision.
5. Database scope enforces table membership in declared coverage; actual SQL execution, tenant/filter coverage, exhaustive absence and physical inventory are still incomplete.
6. Unknown permissions are preserved, but existing policy decisions still trust interpreted summary states. Differing explicit permission facts at the same time already produce an unresolved conflict; broader field/state reconciliation remains future work.
7. Multiple compliant copies with different source IDs still encounter the single-citation output limitation. Missing retained records and canonical-sort/dependency conflicts remain explicit errors.
8. Broad deterministic evidence adapters, general multilingual intent coverage and independent extraction corroboration remain incomplete. Bounded screenshot/ambiguous-intent model execution, revalidated cache replay, reported usage metering and process timeouts are now implemented as described in [MODEL_EXECUTION.md](MODEL_EXECUTION.md).

These concerns are reported for future correctness work, not silently fixed through a structural change or used to make unsupported deletion claims. No organizer-only data or hidden answers were consulted.

## Subsequent measured correctness changes

The preservation results above describe the earlier structural refactor. The next iteration added native JSON/SQL/log/PDF/local-OCR adapters and broadened explicit deletion/audit intent rules. These are correctness changes, not an assertion of full sample byte equivalence. [evaluation/prediction_changes.md](evaluation/prediction_changes.md) explains every changed prediction; [evaluation/iteration_report.md](evaluation/iteration_report.md) reports the accuracy regression caused by rejecting unsupported policy/coverage assumptions.

Native SQL runs only in memory under an SQLite authorizer and instruction bound. Observations retain actual primary/replica table scope; an empty table is not promoted to whole-resource or cross-table absence. This implementation does not yet generate complete subject-scoped negative database queries. Native log correlation uses service and trace IDs; selectors establish ownership, not stored exposure. Missing expected fields are retained as `MISSING`; nulls and unknown permissions are distinct. An anonymized state requires the adapter's explicit identifier fields, rather than absence of parsed fields. This remains a bounded schema interpretation, not proof against all indirect identification.

`EvidenceGap` keeps a source ID, locator, capture time and any visible subject identifiers when a media document cannot be fully assigned a grounded resource. It is separate from observations and never invents a resource ID. Eligible matching gaps block investigation and validation. Blank media creates an unscoped blocking gap. This does not detect every OCR omission, every named person without a parsed identifier, or every unrecognized layout; the media interpreter remains a material correctness limitation. Physical-copy continuity, retrospective availability and single-citation limitations above remain unresolved.
