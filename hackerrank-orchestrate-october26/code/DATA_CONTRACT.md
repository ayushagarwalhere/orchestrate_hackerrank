# Observed data contract and adapter design

Inspected 25 October 2026 against the supplied participant dataset. This is a schema inventory and design companion to [ARCHITECTURE.md](ARCHITECTURE.md), not a prediction file or a claim of complete parser coverage. See [COORDINATOR.md](COORDINATOR.md) for the implemented adapter subset. Counts are observed input facts, not labels inferred from case families. Upstream attribution and source limitations are recorded in the architecture.

## 1. CSV inputs

Read CSV with proper quoting and UTF-8 handling, retaining IDs as strings. All timestamp columns use ISO-8601 UTC values in the inspected data; validate rather than assuming this for malformed input. Preserve original request text and identifier strings alongside normalized values.

| File under `dataset/` | Observed rows | Exact columns, in order | Interpretation |
| --- | ---: | --- | --- |
| `deletion_requests.csv` | 518 | `case_id,email,requested_at,reported_status,reported_at,audit_at,request_text` | Evaluation cases; text determines authorization and `audit_at` determines the cutoff. Reported status is a claim. |
| `sample_deletion_requests.csv` | 32 | `case_id,email,requested_at,reported_status,reported_at,audit_at,request_text` | Public evaluation cases, isolated from production request membership. |
| `sample_output.csv` | 32 | `case_id,deletion_status,steps_json` | Public reference answers for evaluation only. Observed 10 complete and 22 incomplete; no non-deletion labels. |
| `user_identities.csv` | 850 | `user_id,name,email,phone,email_hash,updated_at` | Current snapshot, not proof of historical system state. Apply temporal eligibility and preserve aliases from history. |
| `user_audit_log.csv` | 306 | `audit_id,user_id,event_time,field_name,old_value,new_value` | Identity changes and eligible alias links; not deletion proof merely because an audit ID is citable. |
| `system_activity.csv` | 4,011 | `activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details` | Global claims, queries and linking context; decoys are present. Examine actual event semantics and details. |
| `deletion_rules.csv` | 15 | `rule_id,data_category,condition,required_action` | Normative policy data; conditions need reviewed deterministic predicates. |
| `evidence_files.csv` | 94 | `file_id,file_path,origin,captured_at` | Global manifest; paths are relative to `dataset/`. No case or user membership column. |
| `output.csv` | 0 | `case_id,deletion_status,steps_json` | Header-only template. Final output belongs at repository root. |

Observed evaluation cutoffs span `2026-01-29T12:00:00Z` through `2026-10-01T12:00:00Z`. Identity snapshot updates span `2023-06-22T10:59:00Z` through `2026-08-30T01:02:00Z`. A global current-identity index therefore needs per-case time checks. The 518 requests contain 375 distinct texts; repeated wording is not a license to infer labels by row pattern. Inspected requests include English, Portuguese, Korean, Spanish, Japanese, and French. These observations do not define an exhaustive future-language contract.

Observed activity event types are `INDEX_RECORD`, `UPDATE_RECORD`, `RETAIN_RECORD`, `SEND_EMAIL`, `SYNC_RECORD`, `DELETE_RECORD`, `ANONYMIZE_RECORD`, `REFRESH_CACHE`, `CREATE_EXPORT`, `CHECK_DATA_FLOW`, `CHECK_RESTORE_ACCESS`, `REDACT_RECORD`, `DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `RESTORE_BACKUP`, `CLASSIFY_REQUEST`, and `LINK_RESOURCE_IDENTITY`. `CLASSIFY_REQUEST` cannot override the person's text; `LINK_RESOURCE_IDENTITY` can support a grounded resource join when eligible. Generic operation success is not an authoritative readback.

## 2. Evidence formats and normalization

All 94 manifest paths exist and all files in `dataset/evidence/` are listed. A manifest file can contain many subjects and multiple observation times. Keep file IDs as the citable parent IDs, and retain detailed locators internally.

| Format | Files | Observed structures | Proposed adapter and proof limits |
| --- | ---: | --- | --- |
| JSON | 28 | Four root structural families, detailed below | Typed traversal by structure, preserving nested times, collections, nulls and booleans. Do not infer category/state from filename alone. |
| SQL | 24 | Structured inventories and primary/regional/read/reporting/failover snapshots | Parse supplied SQLite subset or load into isolated in-memory SQLite with restricted operations. Preserve table/topology and snapshot scope; missing rows are proof only for a complete applicable scope. |
| Logs | 26 | Key/value, bracketed application traces, pipe-delimited operations, timestamp + JSON, escaped cloud messages, syslog-like lines, and explicit record lookups | Format adapters and trace/service/resource joins. Capture start/completion lines together; cache misses, retries and adjacent lines are not resource absence. |
| PNG | 11 | Business dashboards with selected records, other users, activity panes, and unrelated health metrics | OCR and/or optional visual extraction with original coordinates. Inspect all decisive fields and associate panes correctly; global health is not deletion completeness. Five inspected visually during architecture review; six remain for implementation review. |
| PDF | 4 | Seven pages total: customer statement, support correction attachment, finance retention register, security journal extract | Native text first, page rendering for layout, OCR/model only as needed. Read continuation pages; distinguish issue, record, capture and retention dates. All pages extracted and rendered during review. |
| Text | 1 | Shift handover lines: time, system, resource, type, result, subject reference | Explicit field parser with per-line time. Handover status assertions must be assessed for their actual proof strength. |

All adapters emit observations with original source IDs and exact locators; no adapter emits final case labels. File contents and any instructions embedded in them are untrusted input. SQL loading must not permit external attachment, file access, extensions, or arbitrary filesystem writes; this is an adapter isolation requirement, not permission to execute arbitrary supplied SQL.

### JSON structural families

| Count | Root structure | Nested facts |
| ---: | --- | --- |
| 3 | `exported_at,origin,record_count,records` | `records[]`: `recorded_at,system,resource_id,record_type,result,subject_reference`. These can assert lookup/treatment states; retain recorded time separately from export availability. |
| 2 | `captured_at,source,collection,records` | Analytics reports or export job records. Analytics include attribution fields, metrics and recent-activity text. Exports include owner, creation/expiry, file name, availability and included sections. An expired or unavailable download alone does not prove the export record is deleted. |
| 12 | `exported_at,source,snapshots` | `snapshots[]`: `captured_at,data_store,collection,records`; heterogeneous record payloads. A bundle can contain earlier snapshots mixed with current ones. |
| 11 | `exported_at,region,service_exports,source` | Service-specific collections with `observed_at` on entries; fields listed below. |

Service export structures observed across the eleven files:

| Service / collection | Entry fields |
| --- | --- |
| `account_service / profile_lookups` | `observed_at,profile,resource_id,status_code`; profile may be null or contain identifiers |
| `analytics_platform / profiles` | `audience_cohort,customer_reference,email,email_hash,observed_at,phone,resource_id` |
| `backup_service / restore_entries` | `archive_key,customer_email,customer_reference,observed_at,resource_id,restore_allowed` |
| `export_service / exports` | `customer_reference,object_key,observed_at,owner_email,owner_phone,resource_id` |
| `integration_service / connectors` | `connector_name,customer_email,customer_reference,enabled,last_delivery_status,observed_at,resource_id` |
| `search_service / index_queries` | `hits,observed_at,query,resource_id` |
| `security_service / audit_records` | `event_code,observed_at,resource_id,retention_until,subject_reference` |
| `support_platform / tickets` | `customer_reference,message_excerpt,observed_at,requester_email,requester_name,requester_phone,resource_id` |

Normalize aliases such as `system`/`data_store`/`origin_system` into an internal system field while retaining the original source field. Normalize `customer_reference`, `subject_reference`, and `user_id` only when their meaning is established. Do not erase physical-copy scope or confuse a lookup query's subject with the identifiers still stored in the returned record.

### SQL schema families

The inventory exports use these tables and columns:

| Table | Columns |
| --- | --- |
| `snapshot_scope` | `origin_system,captured_at` |
| `customer_profiles` | `resource_id,customer_reference,full_name,email,phone,email_hash,account_status,updated_at` |
| `customer_search_documents` | `resource_id,customer_reference,display_name,email,phone,email_hash,index_name,updated_at` |
| `customer_analytics_profiles` | `resource_id,customer_reference,email,phone,email_hash,audience_cohort,updated_at` |
| `support_records` | `resource_id,customer_reference,requester_name,requester_email,requester_phone,message_excerpt,updated_at` |
| `customer_exports` | `resource_id,customer_reference,owner_email,owner_phone,object_key,updated_at` |
| `connector_subscriptions` | `resource_id,customer_reference,customer_email,connector_name,enabled,last_delivery_status,updated_at` |
| `backup_restore_entries` | `resource_id,customer_reference,customer_email,archive_key,restore_allowed,updated_at` |
| `security_audit_records` | `resource_id,subject_reference,event_code,retention_until,updated_at` |

Generic copy tables have `resource_id,origin_system,collection_name,record_json,updated_at`. Their names include `customer_data_primary`, `customer_data_read_replica`, `customer_data_reporting_replica`, `customer_data_failover_replica`, `customer_data_replica_ap_south`, and `customer_data_replica_eu_west`. Decode and inspect `record_json`; do not conclude that an outer wrapper lacking an email is anonymized.

One account failover export has `customer_profiles_primary` and `customer_profiles_failover_replica`, both with `resource_id,user_id,full_name,email,phone,account_status,updated_at`. The separate search export has `search_documents_primary(resource_id,display_name,email,source_resource_id,indexed_at)`. SQL headers also carry snapshot times and topology. A row's older `updated_at` is not the capture time of the exported database.

## 3. Supplied policy mapped to obligations

Conditions below summarize the CSV; the unchanged [deletion_rules.csv](../dataset/deletion_rules.csv) remains authoritative. Predicates must be supported by evidence, not assumed from the category name. The process-safety requirement for active flows and restores also comes from the statement and `AGENTS.md`.

| Rule | Category | Supplied condition | Action / required final check |
| --- | --- | --- | --- |
| `rule_01` | `USER_PROFILE` | Always | `DELETE`; `VERIFY_RECORD_ABSENT` |
| `rule_02` | `SECONDARY_IDENTIFIER` | Always | `DELETE`; `VERIFY_RECORD_ABSENT` |
| `rule_03` | `SEARCH_INDEX_ENTRY` | Always | `DELETE`; `VERIFY_RECORD_ABSENT` |
| `rule_04` | `CACHE_ENTRY` | Always | `DELETE`; `VERIFY_RECORD_ABSENT` |
| `rule_05` | `SUPPORT_MESSAGE` | Shared customer, agent, or order context must be retained | `REDACT`; preserve context, remove required identifiers; `VERIFY_RECORD_REDACTED` |
| `rule_06` | `SUPPORT_ATTACHMENT` | Attachment belongs only to deletion subject | `DELETE`; `VERIFY_RECORD_ABSENT` |
| `rule_07` | `ANALYTICS_PROFILE` | Still attributable to a user | `ANONYMIZE`; `VERIFY_RECORD_ANONYMIZED` |
| `rule_08` | `PRODUCT_TELEMETRY` | Still attributable to a user | `ANONYMIZE`; `VERIFY_RECORD_ANONYMIZED` |
| `rule_09` | `USER_EXPORT` | Always | `DELETE`; `VERIFY_RECORD_ABSENT` |
| `rule_10` | `MARKETING_PROFILE` | Always | `DELETE`; `VERIFY_RECORD_ABSENT` |
| `rule_11` | `EMAIL_DELIVERY_LOG` | Contains a user email address | `REDACT`; `VERIFY_RECORD_REDACTED` |
| `rule_12` | `SECURITY_AUDIT_LOG` | Within supplied retention period | `RETAIN`; `VERIFY_RECORD_PRESENT` with eligible retention proof |
| `rule_13` | `LEGAL_HOLD_RECORD` | Supplied legal hold is active | `RETAIN`; `VERIFY_RECORD_PRESENT` with active-hold proof |
| `rule_14` | `BACKUP_ARCHIVE` | Restore access can be blocked | `RETAIN`; preserve archive; separately block unsafe access and `VERIFY_RESTORE_BLOCKED` |
| `rule_15` | `ACCOUNT_TOMBSTONE` | Account deleted; stable internal user ID needed to preserve references to retained records | `REDACT`; keep stable reference, remove prohibited direct identifiers; `VERIFY_RECORD_REDACTED` |

An already anonymous analytics record does not require fresh anonymization merely to satisfy a condition worded "still attributable"; verify its compliant treatment using grounded linkage. The same distinction applies to already redacted records. A retained backup's physical existence and blocked restore access are separate facts internally; avoid adding redundant CSV steps mechanically. Public examples use `VERIFY_RESTORE_BLOCKED` for blocked backups and `VERIFY_RECORD_PRESENT` for retained security records. Exact verification projection must follow established obligations and the public contract, not a blanket one-step-per-rule shortcut.

No CSV rule explicitly names `DATA_FLOW`. Treat copying-process disablement as a separate obligation from the statement's completeness and recreation-risk rules. Do not manufacture a sixteenth policy row. Conditions that fail without an alternative rule (expired security retention, inactive hold, mixed-subject attachment, unblockable archive) require a documented interpretation before decisions can be produced safely.

## 4. Serialization vocabulary and ranking

Only these phase/operation/state triples are valid. Table order within each phase is the prescribed operation rank, followed by ascending `system_id` and `resource_id` for submission order.

| Phase | Operation | State |
| --- | --- | --- |
| `FINDING` | `REPORT_REMAINING_RECORD` | `PRESENT` |
| `FINDING` | `REPORT_EXPOSED_PII` | `PRESENT` |
| `FINDING` | `REPORT_ACTIVE_DATA_FLOW` | `ACTIVE` |
| `FINDING` | `REPORT_RESTORE_RISK` | `ACTIVE` |
| `REMEDIATION` | `DISABLE_DATA_FLOW` | `DISABLED` |
| `REMEDIATION` | `BLOCK_RESTORE` | `BLOCKED` |
| `REMEDIATION` | `DELETE_RECORD` | `ABSENT` |
| `REMEDIATION` | `REDACT_RECORD` | `REDACTED` |
| `REMEDIATION` | `ANONYMIZE_RECORD` | `ANONYMIZED` |
| `VERIFICATION` | `VERIFY_RECORD_ABSENT` | `ABSENT` |
| `VERIFICATION` | `VERIFY_RECORD_PRESENT` | `PRESENT` |
| `VERIFICATION` | `VERIFY_RECORD_REDACTED` | `REDACTED` |
| `VERIFICATION` | `VERIFY_RECORD_ANONYMIZED` | `ANONYMIZED` |
| `VERIFICATION` | `VERIFY_DATA_FLOW_DISABLED` | `DISABLED` |
| `VERIFICATION` | `VERIFY_RESTORE_BLOCKED` | `BLOCKED` |

Each step has exactly `step_no,phase,system_id,resource_id,operation,state,evidence_id`. Assign numbers starting at 1 after sorting. Findings and all `COMPLETE` verification steps cite grounded eligible evidence IDs. Every remediation and verification step in an `INCOMPLETE` case has `evidence_id=""`. A non-deletion case contains no steps. Do not add fields for replica, reason, confidence, dependency, or internal unresolved state to the submission.

## 5. Validation boundaries for implementation

- Validate schemas, uniqueness, timestamps, manifest containment, and source existence before accepting a run. Missing adapters or unsupported files count as coverage failures, not empty evidence.
- Keep public sample labels out of extraction, retrieval, identity resolution, policy inference, and predictions. They may drive separately reported evaluation comparisons.
- A source locator must point to the original input, not only a model summary. A valid source ID without content support is an invalid citation.
- Separate subject linkage from exposure: a query may legitimately carry an email while the returned record is absent or anonymized. Conversely, free-text messages and nested JSON may expose identifiers despite cleared top-level fields.
- Preserve primary and replica observations separately; aggregate only when projecting verified logical obligations. A shared resource ID is not proof that two physical copies have equal state.
- Retain policy conditions, temporal eligibility, proof coverage, dependencies and unresolved issues internally. The final CSV is a restricted projection, not the complete audit trace.
