# Local changes to the authorized baseline

The implementation was independently reproduced first: all 518 rows and the
published output hash match. The previous independent implementation and its
reports were preserved by hash.

| Change | Reason and verification |
| --- | --- |
| Eligible snapshot plus interval-based identity values | Later A→B→C changes must not introduce intermediate B into an earlier identifier set. Only the earliest later boundary may reconstruct the live value when the snapshot itself is later, preserving the upstream retrospective mode. |
| Reject malformed/short phone identifiers | Preserve international country-code digits; placeholders and short strings must not become shared identity keys. |
| Reject observation time after file capture | An impossible future-in-capture observation must not become usable merely because a later audit passes its timestamp. Image clocks are preserved, not clamped. |
| Persistent account-absence fallback | If no in-window proof exists, an earlier eligible absence can still establish an already-deleted account. A newer eligible presence or later creating/sync/import/restore claim invalidates the fallback. This uses the authoritative-coverage interpretation and does not establish ownership. |
| Reject uncited COMPLETE verification | The inherited validator accepted empty evidence. The candidate supplies eligible absence citations for all three affected rows and the validator now rejects this omission generally. |
| Offline by default, explicit live inference | A configured API key must not silently cause billable calls during ordinary replay or unit tests. |
| Bind image facts to SHA-256 | Changed artifacts cannot silently reuse extraction from the same file ID. All 11 imported fact files retain author/model attribution. |
| Code-only package and external prediction backups | Follow the supplied three-file upload contract and keep dataset, environments and generated output caches out of the source archive. |
| Bounded coordinator and typed tools | The CLI now runs AuditAgent through explicit load/extract/index/investigate/compile/validate/publish contracts. The evidence index is built once per prediction run. |
| Validate before atomic publication | A failed candidate cannot replace the previous output. Tool events and aggregate counts make the actual execution inspectable without including customer text or secrets. |
| Versioned, constrained live prompts | New v3 image extraction preserves unknown fields; unresolved extraction fails. Intent text is JSON-encoded and fallback responses accept only the declared schema. Historical cached extraction is not relabeled as a new run. |
| Cache validation and model budget | Validate cache hits as well as live responses; reject corrupt cache, use atomic writes and bound new adapter invocations to 32 by default. |
| Confined evidence tools | Reject manifest escapes and duplicate source IDs; prohibit SQLite external attachment and unsafe pragmas/functions, quote table names, and bound SQL work. |
| Readability and review guide | Document the implemented architecture, authority boundaries and known limitations. Preserve the actual transcript; add an explicitly editorial guide rather than rewriting user prompts. |

No sample answers, copied prediction CSV or case-specific correction mapping was
added to prediction logic. The persistent-absence rule changes evidence fields
for case_45, case_126 and case_127; those IDs occur only in post-prediction reports,
not in the rule. Sample mismatches remain case_18, case_20 and case_23.

The three-citation candidate is a reasoned improvement in evidence completeness,
not a demonstrated external evaluation gain. Its pre-request coverage semantics and the
upstream workflow/naming/retrospective membership assumptions remain explicit
review considerations. No author permission is represented as event approval.
