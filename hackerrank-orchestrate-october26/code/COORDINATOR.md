# Implemented coordinator and tool boundaries

The executable entry point is `python -B code/main.py` (Python 3.10+, standard library only). It constructs the real `AuditAgent` with seven default tools. The coordinator is not an unused architecture wrapper: the CLI has no alternative prediction/publication route.

The original HackerRank / InterviewStreet scenario, dataset, policy and vocabulary remain attributed in [ARCHITECTURE.md](ARCHITECTURE.md). The implementation adds participant workflow code without changing supplied data or upstream policy.

The evidence model now separates observations, ownership links, inference candidates and assumptions. See [EVIDENCE_REASONING.md](EVIDENCE_REASONING.md) for identity normalization, physical/table scope, explicit unknowns, preserved behavior and unresolved correctness concerns.

The model boundary is now constrained to screenshot facts and ambiguous intent. See [MODEL_EXECUTION.md](MODEL_EXECUTION.md) for versioned prompts, strict schemas, opt-in execution, cache validation, process timeouts and actual usage accounting.

## Run sequence and effects

| Tool | Typed input → output | Permitted tool effects |
| --- | --- | --- |
| `load_inputs` | `LoadInput` → `LoadedInputs` | Read the six participant CSV inputs and manifest-contained evidence files. No sample labels, hidden files or generator inputs. |
| `extract_evidence` | `ExtractionInput` → `ExtractedEvidence` | Native parsing; local OCR subprocess and verified temporary image writes/removal under `runs/.ocr`; optional bounded screenshot inference and cache reads/writes. No default model/network calls or source-file writes. |
| `index_evidence` | `IndexInput` → `EvidenceIndex` | In-memory indexing only. Validate full artifact coverage and observation provenance first. |
| `investigate` | `InvestigationInput` → `Investigation` | In-memory joins/reconstruction; optional bounded ambiguous-intent inference and cache reads/writes. |
| `compile_plan` | `CompilationInput` → `CasePlan` | In-memory policy evaluation, findings, remediation, verification and precedence checks. |
| `validate_output` | `ValidationInput` → `ValidatedOutput` | In-memory independent plan, evidence, schema and CSV round-trip checks. No output writes. |
| `publish_output` | `PublicationInput` → `Publication` | Write a temporary file next to the selected CSV, flush/fsync and atomically replace that CSV; remove the temporary file on failure. Never write into the dataset. |

Contracts are frozen typed objects in `audit_agent/contracts.py`. The coordinator checks the declared contract and input/output runtime types for every invocation. These declarations constrain integration and tests; they do not sandbox trusted Python extension code. The JSONL telemetry sink separately declares `write_telemetry`, and its destination must be outside the dataset and distinct from the CSV.

Load, extraction, and indexing run once, before the request loop. Each investigation receives the same immutable `EvidenceIndex`, containing a typed identifier index over ownership links and resource/source indexes over observations. Its mappings are read-only and its records are frozen. No per-case index rebuild is hidden in investigation. Eligible identity aliases are computed per cutoff; future facts cannot introduce graph edges. Requests, rule predicates and evidence are never passed to a model as a final-decision prompt.

`ToolSet`, `OptionalExtractor`, telemetry sink, and monotonic clock are replaceable. Tests replace one tool using `dataclasses.replace` while retaining the remaining real tools. This permits fault injection at extraction, indexing, compilation, validation and publication boundaries without changing the CLI or introducing another implementation path.

## Optional extraction contract

Native extraction supports explicit JSON readback records with root fields `exported_at,origin,record_count,records` and the supplied text handover format. Records require `recorded_at,system,resource_id,record_type`; missing state results remain unknown and missing subject references create no ownership link. Optional condition facts, retention date, physical/table scope, permission booleans and explicit downstream keys are supported. Unknown structure or extra fields require an adapter rather than being silently discarded. Invalid JSON or mismatched record counts are extraction errors.

The unrestricted `--extractor` CLI is retired and rejected. `--inference-provider` and `--inference-model` configure validated cache-only replay. `--allow-live` and `--model-client module_name:factory_name` explicitly enable a trusted low-level client inside the bounded worker runtime. Code binds its strict JSON facts into `ArtifactExtraction`; the client cannot provide final citations or executable plans. No provider/model is selected implicitly. Programmatic `OptionalExtractor` injection remains for trusted deterministic adapters/tests, not as an unmetered production model path.

An artifact exposes only its participant-visible ID, suffix, capture time, in-memory bytes, and SHA-256. It exposes no dataset path, sample labels, credentials, or coordinator tools. The returned `ArtifactExtraction` must bind the same ID and digest, contain a tuple of typed `Observation` objects, and explicitly assert `complete=True`. Partial extraction, wrong source binding, invalid types/states/times/locators, provider exceptions and missing adapters all abort the run. An untyped empty provider result cannot become successful deletion. A fully inspected artifact may legitimately return an explicitly complete empty observation tuple, but an authorized case with no grounded resource proof remains unresolved.

Adapter migration: each `Observation` now requires a separate `captured_at` as well as observation and availability times. Its old `subjects` tuple is removed. Emit ownership separately through `ArtifactExtraction.ownership_links`; optional candidates and assumptions also have separate tuples. There is no implicit conversion of an old subject tuple into ownership. State-only and ownership-only packets are valid when fully inspected, but neither layer substitutes for the other in investigation or validation.

Observation conditions must be grounded in the source. Allowed condition witnesses are `shared_context`, `subject_only`, `active_hold`, `restore_blockable`, and `tombstone_reference_required`. Merely emitting a syntactically valid witness does not prove the provider interpreted the artifact correctly; a reviewed adapter must check quotations/coordinates against the source and inspect all pages/chunks. The coordinator validates the envelope and temporal/provenance structure, not visual truth. Arbitrary unreviewed model output is not a trusted extraction adapter.

Each approved screenshot or ambiguous-intent invocation uses a shared model runtime with explicit invocation, call, retry, token, byte and wall-clock limits. Live client setup/calls run in a spawned process and are terminated on timeout. Usage is metered before response validation; unknown usage and corrupt caches stop the run. Versioned, source-bound cache entries are revalidated and never overwritten or relabeled. See [MODEL_EXECUTION.md](MODEL_EXECUTION.md) for the exact retry policy, client responsibilities and remaining limitations.

## Publication and errors

All tools must succeed before publication. An extraction failure short-circuits indexing, investigation, compilation, validation and publication. Existing output is preserved. Unsupported formats and unresolved intent/identity/state/policy are errors, never `COMPLETE`, empty findings, or a fallback `NOT_APPLICABLE` row.

The validator checks exact request membership, duplicates, legal phase/operation/state combinations, all required final checks, numbering, canonical order, citation support and cutoff, and empty future evidence IDs. It also rechecks dependency precedence independently of the compiler. Flow/restore safety controls precede dependent records; record copies precede their sources where required. A dependency inversion against the required CSV sort blocks publication.

Only a `ValidatedOutput` byte payload with the correct digest and expected row count reaches the publisher. The temporary file lives on the destination filesystem so `os.replace` provides atomic replacement; failed replacement preserves the existing destination. This is an offline plan, never live deletion or a claim that future checks ran.

## Telemetry and privacy

The default log is `runs/tool_outcomes.jsonl`. Each record has a generated run ID. Tool outcome records include a fixed tool name, success/failure, monotonic duration in milliseconds, allowlisted integer counts, and a fixed failure enum. Summaries aggregate calls, durations, stage-qualified counts and failure types. Counts are stage-qualified so rows validated and rows published are not incorrectly summed as separate customer requests. Extraction failures retain processed-artifact/observation counts and attempted external-call counts.

No customer text, email, phone, source contents, request IDs, filesystem paths, credentials, exception messages, tracebacks, or plugin module names enter these records. Sensitive dataclass payloads are excluded from repr as an additional precaution. CLI output is restricted to aggregate telemetry, fixed error codes, published row count and output digest. This policy covers framework logging; trusted plugins must separately avoid logging source content or credentials through their own handlers.

Telemetry sink errors before publication also abort. The CSV and JSONL log are separate filesystem transactions: a telemetry failure after successful CSV replacement cannot undo that replacement, and the CLI reports the telemetry failure. This is distinct from extraction failure, which always precedes publication.

## Commands and present coverage

From the repository root:

```text
python -B code/main.py
python -B code/main.py --inference-provider PROVIDER --inference-model MODEL --model-cache runs/model-cache
python -B code/evaluation/main.py
```

CLI options also include `--dataset`, `--output`, `--telemetry`, and `--expected-cases`. The normal challenge run expects exactly 518 cases. A smaller expected count is intended for independent fixture datasets, never for silently truncating the challenge input. Defaults resolve from the repository rather than the current working directory.

The earlier full-dataset smoke loaded 518 requests, 850 identities, 4,011 activities and 94 artifacts, then stopped at unsupported extraction. Measured iteration has since added native structured JSON, bounded in-memory SQL, service-log and PDF adapters plus offline Windows OCR. This is extraction-format coverage, not proof of complete semantic coverage. Empty/partial image interpretation with visible unrepresented identifiers creates a source-bound `EvidenceGap`; eligible relevant gaps block investigation and independent validation. Missing analytics fields remain unknown, and policy witnesses are not fabricated from event names. Optional intent interpretation only handles grammar-unresolved requests under strict span and qualifier rules; uncertainty remains a failure. No root `output.csv` has been produced. See [evaluation/iteration_report.md](evaluation/iteration_report.md) for the current 32-case results and remaining gaps.

The coordinator fixtures exercise actual successful publication as well as failed extraction, malformed provider results, incomplete coverage, future evidence, identity history, replica conflicts, missing retention, invalid plans/citations, tool-contract mismatch, telemetry failure and atomic replacement failure. See [evaluation/evaluation_report.md](evaluation/evaluation_report.md) for measured results and limits.
