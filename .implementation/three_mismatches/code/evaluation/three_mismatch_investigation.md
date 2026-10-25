# Three remaining sample mismatches — 25 October 2026

## Decision

No evidence-supported prediction correction was found. The two requested security resource IDs do not occur in the inspected participant sources. The two requested account activities contain no subject identifier or correlation that distinguishes ownership. All three mismatches remain unresolved. No expected resource ID, case mapping or extra expected step was added to prediction logic.

This investigation adds a reusable read-only participant-source inspection command and independent boundary regressions. Production linking, policy, workflow assignment, source data, historical extraction caches and attribution remain unchanged. The account mismatch exposes an inherited unsupported tie-break; preserving it here is behavior preservation, not endorsement of its correctness.

## Scope and reproducible searches

Predictions were frozen before opening public reference answers in this investigation. The user had supplied the three targets and earlier evaluation was already known, so this is targeted investigation, not a blind accuracy experiment. Participant searches exclude `sample_output.csv`, prediction outputs, evaluation fixtures and organizer/generator files.

From the repository root, with Python and the documented dependencies installed:

```powershell
rg -n -e '\b(audit_record_6645|audit_record_5569|account_410|account_7015|activity_3660|activity_3662)\b' dataset/evidence dataset/system_activity.csv dataset/user_identities.csv dataset/user_audit_log.csv dataset/evidence_files.csv
python -B code/evaluation/inspect_participant_evidence.py --target audit_record_6645 --target audit_record_5569 --target account_410 --target account_7015 --target activity_3660 --target activity_3662 --out diagnostics/three-mismatch-investigation/participant_search_repeat.json --render-dir diagnostics/three-mismatch-investigation/rendered-repeat
python -B code/evaluation/inspect_participant_evidence.py --target user_50 --target user_48 --target user_23 --target mori.ren@gmail.com --target akosua.gyasi@gmail.com --target thandiwe.m6866@zoho.com --out diagnostics/three-mismatch-investigation/subject_search_repeat.json
python -B code/main.py --no-llm --out diagnostics/three-mismatch-investigation/cli_518_repeat.csv --trace diagnostics/three-mismatch-investigation/cli_trace_repeat.json
python -B -m pytest code/tests -q
```

The inspection command requires a new output filename. It records source hashes, manifest capture times, raw line locations, decoded JSON pointers, SQL table/row/column locations, PDF page/text-line locations, errors and media requiring visual review. Numeric suffix hits and Unicode-normalized hits are separate from exact identifiers. SQL execution is in an isolated in-memory database with external database attachment and dangerous operations denied and an instruction budget. This is an investigation utility, never an input to the predictor.

The scan covered **101 files: all 94 manifest artifacts and seven participant CSVs**, with zero inspection errors. All **24 SQL captures, 127 tables and 969 rows** (including scope metadata) were inspected, including decoded `record_json` values. There are no declared SQL foreign keys; implicit relationships still require examination. Subject searches used stable user IDs, current/historical emails, phone digits with country codes, hashes and resource/reference fields. They found no SQL rows bearing any of these three subjects' canonical identifiers. Name strings and document labels were also reviewed; numeric labels alone were never treated as identity.

To repeat the remaining identifier searches, append `--target` arguments for each raw phone, canonical phone and full hash in the subject table below. The same command inspects all SQL rows, JSON scalars and PDF text regardless of what the runtime parser indexed. SQL row locations are scan ordinals, not guaranteed persistent primary keys; retain the source hash when reproducing a result.

All seven pages of four PDFs were rendered and inspected, together with all eleven supplied screenshots. Zero textual hits does not establish visual absence; the separate pixel review supports the narrower conclusion that no printed target or subject-to-target relationship was found in those supplied artifacts. Referenced external attachments that are not supplied remain unavailable.

Artifacts in `diagnostics/three-mismatch-investigation/` record the source search, SQL subject matches, correlated log groups, all 20 unresolved ledger references, rendered pages, frozen predictions, actual CLI trace and row-by-row prediction comparison. Diagnostics are ignored by Git; the commands and findings here remain the durable record.

### Exact resource inventory outside answers

| Target | Participant source occurrence | Ownership or state established? |
|---|---|---|
| audit_record_6645 | None found, including decoded SQL/JSON and rendered media | Neither ownership, presence nor retention interval |
| audit_record_5569 | None found | Neither ownership, presence nor retention interval |
| account_7015 | system_activity.csv line 3661, activity_3660 | A failed delete claim naming the resource; no subject or resulting state |
| account_410 | system_activity.csv line 3663, activity_3662 | Same limitation |

The forensic JSON contains ten exact hits because raw CSV lines and decoded field representations repeat the same two physical activity rows. These are not ten independent witnesses. Neither account has an indexed observation or catalog ownership link. Both security IDs have no indexed observation, catalog link or activity.

Suffix decoys cannot fill the gap: `support_5569` belongs to Ren Mori's support trace; `CS-5569` appears in regional SQL support rows for user_405/Lucia Garcia, not Akosua. The SQL locations are `customer_data_regional_replicas_20260330.sql` lines 41, 77 and 112. `account_41038` in the September 30 runtime export is a different, later resource. `retry_in_ms=410` in the August 24 log line 12 is a duration. None establishes the requested association.

## Subject provenance and clocks

CSV row locations below use physical line numbers including the header. These CSVs supply event/update times but no separate capture time; treating their availability as their event time is inherited and remains an assumption. UTC is used throughout. Sample request rows establish the question and cutoff, not ownership of an arbitrary resource.

| Request / source | Subject identifiers | Timing and history |
|---|---|---|
| case_18; sample_deletion_requests.csv:19; user_identities.csv:51 | user_50, Ren Mori, mori.ren@gmail.com; phone +81 90 6947 3342; hash 17813ce08076a05a5d763fa691e2df7f241b610f34b10a81f82544d06f74a4dd | Requested Sep 6 11:00, reported COMPLETE Sep 9 11:00, cutoff Sep 26 11:00. Identity updated Jan 28 18:46:59. audit_169 at user_audit_log.csv:170 records old phone +81 90 2367 3149 → current phone at that same update time. |
| case_20; sample_deletion_requests.csv:21; user_identities.csv:49 | user_48, Akosua Gyasi, akosua.gyasi@gmail.com; +233 24 014 4504; hash fe822c22457cb0bf2c7b96098b2756bff294e939c93a5eb55b3c6438be0245ad | Requested Sep 8 11:00, reported NOT_STARTED Sep 9 11:00, cutoff Sep 26 11:00. Identity updated May 10 2025 10:36. No supplied identity-history rows. |
| case_23; sample_deletion_requests.csv:24; user_identities.csv:24 | user_23, Thandiwe Mthembu, thandiwe.m6866@zoho.com; +27 72 861 6082; hash 5a2cb16db260ce9c10ffddc80e9ebc9b56ace8b3160a15ffe71887ca431c04d3 | Requested Sep 2 12:00, reported NOT_STARTED Sep 5 12:00, cutoff Sep 15 12:00. Identity updated Feb 2 18:01. No supplied identity-history rows. |

Canonical phone search values are 819069473342 / historical 819023673149, 233240144504 and 27728616082. Country codes are retained. Missing historical rows do not establish that no other identifiers ever existed.

## Positive associations actually supported

The following are supported subject-to-resource associations, not proposed links to the missing targets. No conflicting subject appears in these cited records, but none bridges to the requested security IDs or account candidates.

`evidence_94`, `evidence/logs/resource_lookup_trace_20260926_103856.log`, capture **2026-09-26T10:38:56Z**. Pairing uses explicit trace ID, service and resource, not event adjacency alone. Both the lookup and result are inspected; a result containing the email is stronger than a lookup selector alone.

| Subject email | Resource / interpreted state | Exact lines / trace | Observation time, Sep 26 UTC |
|---|---|---|---|
| mori.ren@gmail.com | support_5569 / IDENTIFIABLE | 10–11, rb-075944-005 | 07:59:44 |
| mori.ren@gmail.com | analytics_037 / IDENTIFIABLE | 22–23, rb-085749-011 | 08:57:49 |
| mori.ren@gmail.com | data_flow_4890 / ACTIVE | 24–25, rb-090511-012 | 09:05:11 |
| mori.ren@gmail.com | search_4013 / PRESENT | 52–53, rb-102312-026 | 10:23:12 |
| akosua.gyasi@gmail.com | search_4262 / PRESENT | 8–9, rb-075713-004 | 07:57:13 |
| akosua.gyasi@gmail.com | data_flow_1770 / ACTIVE | 40–41, rb-095254-020 | 09:52:54 |

No security-service trace group carries either subject's identifiers, and no unresolved ledger reference supplies the missing audits. The existing inferred accounts for these cases, account_5521 and account_5037 respectively, use L5 unique workflow timing and account absence from evidence_05. These are inherited inference candidates, not direct ownership proof and not security links.

For Thandiwe, `evidence_92`, `evidence/records/service_resource_export_20260915_114455.json`, captured **2026-09-15T11:44:55Z**, contains:

| Location | Resource | Observation time | Subject-bearing evidence / uncertainty |
|---|---|---|---|
| /service_exports/export_service/exports/0 | export_7364 / PRESENT | Sep 15 09:39:19Z | owner email matches; no account parent reference |
| /service_exports/search_service/index_queries/2 | search_898 / PRESENT | Sep 15 10:08:28Z | email/query matches; no source_resource_id linking either candidate account |

`evidence_02`, `customer_data_snapshot_bundle_20260917.json`, also contains email-bearing export_7364 at `/snapshots/5/records/0`, email/user_23-bearing search_898 at `/snapshots/7/records/1`, and user_23-bearing audit_record_4128 at `/snapshots/8/records/2`. Observation time is Sep 15 12:00Z, but capture is **Sep 17 12:00Z**, after this cutoff. It is not cutoff-available ownership evidence. Existing membership resolution is retrospective; this remains an inherited limitation. Even retrospective use supplies neither account target nor either missing security ID.

## case_23: activity_3660 versus activity_3662

The exact participant rows are:

```text
system_activity.csv:3661
activity_3660,2026-09-05T11:01:52Z,DELETE_RECORD,deletion_worker,account_service,account_7015,FAILED,Deletion worker submitted primary profile account_7015 to account_service.
system_activity.csv:3663
activity_3662,2026-09-05T11:10:55Z,DELETE_RECORD,deletion_worker,account_service,account_410,FAILED,Deletion worker submitted primary profile account_410 to account_service.
```

Neither row includes user ID, name, email, phone, hash, request ID, workflow ID or trace correlation. Separate capture times are unspecified. FAILED is an operation result, not proof of ownership or current presence. Neither timestamp distinguishes the subject. No supplied SQL join, current/historical identifier, catalog link, log correlation, unresolved reference or rendered artifact bridges either activity to user_23.

The inherited window is reported_at minus 90 minutes through plus 15 minutes: **Sep 5 10:30–12:15Z**. Six account deletion anchors lie in it: account_294/PARTIAL at 10:50:10, account_8832/PARTIAL at 10:52:20, account_7015/FAILED at 11:01:52, account_6440/SUCCESS at 11:01:53, account_410/FAILED at 11:10:55 and **account_9155/FAILED at 11:12:36 (activity_3663)**. The third failed account is also unowned; it must not be silently excluded.

Three deletion requests share the reported time and NOT_STARTED claim: case_23/user_23, case_547/user_547 (a.patel22@yahoo.com) and case_548/user_548 (fernandez.sofia@icloud.com). Sorting numeric case IDs and then event times currently assigns 7015, 410 and 9155 in that order. This explains the result; it does not justify the association. Without additional ownership constraints there are six possible one-to-one permutations. Renaming numeric case labels changes the heuristic result without changing subject evidence, as the new synthetic regression demonstrates. Swapping case_23 to 410 would also displace another request without evidence.

`evidence_51`, `customer_data_snapshot_bundle_20260915.json`, captured and observed **Sep 15 12:00Z**, contains an explicitly empty customer_profiles snapshot at snapshot 0. The index records its physical scope as `/snapshots/0/customer_profiles`. Its scoped omission supports ABSENT for either account target under the inherited authoritative snapshot model. Both synthetic omission observations have **empty subject link keys**. It establishes state within that declared scope, not which account belongs to Thandiwe. It does not prove global absence across unspecified systems or physical copies.

Required missing relationship: an eligible subject-bearing account record, explicit catalog edge, historical identity-to-account reference, or authoritative request/workflow correlation joining user_23 to account_410 or account_7015. An exclusion argument would additionally require a supported exhaustive one-to-one candidate set; timing and labels alone do not provide it.

## case_18 and case_20: retained security records

Policy source `deletion_rules.csv:13`, rule_12, requires RETAIN for a SECURITY_AUDIT_LOG **within its supplied retention period**. A rule cannot manufacture a resource ID, its owner or its retention interval. There is no participant witness for audit_record_6645 or audit_record_5569, so neither expected verification can be supported by inserting the reference ID.

There is a real positive retained-security example for a different subject: `evidence_55`, `security_retention_extract.pdf`, page 1, captured **Sep 5 06:30Z**, signed extract CJX-20260905-0630, explicitly pairs **audit_record_003 with user_03**, recorded Aug 25 04:03Z, retained until Aug 25 2027 04:03Z. `evidence_37`, the Sep 5 07:00Z security screenshot, displays that subject's audit records and selects audit_record_003. Neither source names user_50, user_48, 6645 or 5569. This is evidence of how an association can be established, not a template for inventing other records.

The precise missing evidence is twofold for each expected ID: (1) a subject-bearing ownership edge to the current or historical identifiers above, and (2) an eligible resource/state witness including the applicable retention period. No reliable general correction can recover an entirely absent ID from policy text or suffix coincidence. The public expected INCOMPLETE verification has an empty citation because it is future work; that serialization permission still does not authorize inventing inventory.

## Rendered documents and unresolved references

The complete visual review included screenshots evidence_04, 09, 14, 19, 23, 28, 32, 37, 42, 46 and 60, and PDFs evidence_18 (2 pages), 27 (2), 55 (1) and 58 (2). Subject numbers in artifacts are not case numbers: the account-history PDF evidence_18 concerns Ingrid Dahl/user_18, not case_18's Ren Mori/user_50; screenshot evidence_19 concerns Omar Darwish/user_20, not case_20's Akosua/user_48.

All 20 unresolved ledger references were reviewed separately from observations. They comprise two unlabeled connectors in evidence_14, six order references plus an unclassified tombstone_17 reference in evidence_27, seven external filenames in evidence_46, CS-4827 in evidence_58 and three resource refs in evidence_57. The legal register's six printed order subjects are user_08, 12, 17, 21, 24 and 29. The support correction attachment concerns Priya Raman/support_001/CS-4827. The SQL resource refs are account_006, account_8814 and account_4203 in `search_documents_primary` rows 1–3. No reviewed reference carries any target subject identifier or the requested resource ID. Missing external attachment contents remain missing; they cannot be assumed irrelevant or silently converted into a match.

## Validation and remaining limitations

The full suite passes **247 tests**, including 14 new independent tests with synthetic identifiers. These cover exact namespace/numeric boundaries, escaped JSON locations, explicit SQL relationships, rejection of SQL external effects, exclusion of answer files, failed extraction versus zero hits, subject-bearing ownership overriding order, case-renumbering exposing the timing heuristic, blanket absence without ownership, and failed deletion without a state witness. They do not assert the three supplied expected associations.

Every one of the **518 target requests** was compared for status and complete serialized steps: **zero changes**, byte-identical CSV SHA-256 `e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc`. The actual CLI independently produced the same bytes and validated all 518 rows. The combined 550 target/public request freeze is also byte-identical, SHA-256 `10a0adaba9d7837037ff41f7553e01a2f38e0b3243c62072efe2c69894ba061f`. The comparison writer uses the baseline row order and LF encoding; an initial diagnostic writer used CRLF and a different combined row order, yielding byte differences despite identical rows. It was corrected to compare the actual serialization contract.

Only after freezing both prediction runs were public reference answers reopened. Status accuracy remains **32/32**, full-case exact accuracy **29/32**; 190 semantic steps match out of 191 predicted and 193 expected. case_18 and case_20 each lack the requested retained-security verification; case_23 substitutes account_7015 for account_410 in future absence verification. No other step, evidence, operation, state, numbering or order changes. All three statuses remain INCOMPLETE. No hosted inference was used.

The ledger still has 20 unresolved source references; 22 unresolved case references and 137 states lacking a current witness are broader inherited issues, outside this targeted investigation. Timing windows, reported-result filtering, numeric order tie-breaks, naming fallback, retrospective membership and logical snapshot coverage remain assumptions. Search failure does not prove deletion, prove that a hidden answer is wrong, or rule out an unavailable relationship. This investigation establishes the precise evidence gap and reproducible searches; it does not claim the mismatches are fixed.
