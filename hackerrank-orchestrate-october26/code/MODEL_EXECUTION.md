> This document describes the preserved independent profile (`code/proof_main.py`, package `audit_agent`). The default CLI is documented in ARCHITECTURE.md and README.md.

# Constrained model execution

Implemented 25 October 2026. Models are optional and admitted for exactly two purposes: PNG screenshot fact transcription and interpretation of request text that the deterministic intent grammar cannot resolve. SQL, logs, JSON records and PDF documents never fall back to a model. Final deletion status, identity/resource admission, citations, policy operations, ordering, validation and publication remain code decisions.

The challenge/data attribution in [ARCHITECTURE.md](ARCHITECTURE.md) is unchanged. No provider SDK, model recommendation or hosted client is selected implicitly. Tests use fake clients only.

## Versioned prompts and schemas

- [prompts/screenshot.v1.md](prompts/screenshot.v1.md) treats image/document contents as untrusted data. It requests visible literal fields, exact supporting text, pixel bounds and a complete/uncertain flag.
- [prompts/intent.v1.md](prompts/intent.v1.md) treats customer messages as untrusted data. It requests action facts, affirmation/negation/conditional qualifiers and exact Unicode code-point spans.
- `audit_agent/model_schemas.py` contains the strict JSON schemas. Every property is required, absent literal facts use null, and extra properties are forbidden. Validation rejects duplicate JSON keys, non-finite numbers, wrong types (including booleans used as integers), extra properties, out-of-range coordinates, excessive arrays/strings and invalid semantic support.

The model request carries the configured provider/model, trusted system prompt, response schema, untrusted bytes, MIME type, output-token cap and timeout in separate fields. Client drivers must preserve these roles and request strict structured output when supported. They must not attach tools, execute returned code or concatenate source content into system instructions. Local validation remains mandatory even when a provider offers a strict response mode.

Neither schema contains a final deletion status, source ID, hash, capture time, evidence citation, operation or executable plan. The model cannot set those fields: extra fields are rejected. Screenshot result strings are interpreted by code; executable-looking text is never run. An uncertain/partial transcription or an unresolved/conditional intent cannot authorize publication.

## Code binds provenance and identifiers

`ScreenshotAdapter` verifies PNG signature/dimensions and recomputes the input hash before inference. Code binds each admitted observation/link to the original manifest source ID, SHA-256 and capture time, plus prompt version/hash, schema version/hash and validated response hash. The final citation is still selected by the deterministic compiler, not by the model. Capture time is not read from model JSON. When no observation time is visibly supplied, capture-time use is recorded as an explicit assumption.

Models transcribe literal resource/system/category/subject strings, not authoritative identifiers. Every non-null field must occur in the returned supporting visible text and its box must fit the source dimensions. Resource IDs must already be grounded in structured evidence or activity; subject identifiers must match the current/historical typed catalog. No image-only invented ID is automatically admitted. System/category defaults can be supplied only by code's grounded context; ambiguity remains unknown/unresolved. Context availability participates in observation availability, preventing a later catalog from silently backdating a screenshot fact.

The catalog digest is part of the cache key. This deliberately conservative admission rule limits discovery of genuinely new image-only resources until an independent grounding/review path exists. Quoted text and a known-ID check do not independently prove that the pixels contain that text: a model can still misread or hallucinate an already-known ID or state. The framework does not claim an OCR/visual truth guarantee.

`ModelIntentInterpreter` is called only after deterministic classification is unresolved. It refuses to override known deletion/non-deletion decisions and does not use models to resolve known conditional, quoted, marketing-only or partial-scope requests. Exact quoted spans are checked against the original message. Code applies the action/affirmation/negation/conditional rules and binds the resulting assessment to the case, message hash, message time and active prompt/schema hashes. The output validator checks that binding and repeats the decision rules without another model call. Ambiguous semantic interpretation can still be wrong despite exact quotes; uncertain facts fail closed.

## Live opt-in and limits

Default execution has no model runtime and makes no model calls:

```text
python -B code/main.py
```

An explicit provider/model profile enables validated cache-only replay:

```text
python -B code/main.py --inference-provider PROVIDER --inference-model MODEL --model-cache runs/model-cache
```

Only an explicit live flag permits cache misses to invoke a configured client:

```text
python -B code/main.py --inference-provider PROVIDER --inference-model MODEL --model-client module_name:factory_name --allow-live --model-cache runs/model-cache
```

`module_name:factory_name` is trusted executable configuration. The zero-argument factory returns a client with `complete(ModelRequest) -> ModelReply`. Provider credentials are read by that driver from environment variables; they are never passed in model payloads, caches, reports or telemetry. No hosted provider implementation is bundled. Merely naming a client does not enable live calls or import its factory on a cache hit/miss in offline mode.

The old unrestricted CLI `--extractor` option is intentionally rejected. It allowed model use on arbitrary formats and bypassed execution limits. Programmatic `OptionalExtractor` injection remains for trusted deterministic adapters and tests; arbitrary Python tool/client injection is not an OS security sandbox and must not be used as an unmetered model path.

| Limit / CLI option | Default | Enforcement |
| --- | ---: | --- |
| `--max-model-invocations` | 32 | Includes approved screenshot/intent adapter invocations and cache hits |
| `--max-live-calls` | 16 | Global attempt cap, including retries |
| `--model-retries` | 1 | At most two attempts per request; configured retry count must be 0–2 |
| `--model-timeout` | 20 seconds | Worker setup/invocation/response wait; worker terminated on timeout |
| `--model-total-seconds` | 120 seconds | Shared run deadline; no further invocation after exhaustion |
| `--max-model-tokens` | 100,000 | Aggregate actual reported input/output tokens; exhaustion aborts publication |
| `--max-output-tokens` | 2,048 | Sent to the client; actual reported output is also checked |
| Input bytes / response bytes | 16 MiB / 64 KiB | Bounded source payload and raw model JSON |

Live provider setup and calls execute in a spawned worker. A timed-out worker is terminated, then killed if necessary; cleanup waits add at most one second under normal OS process-control behavior. A blocked filesystem or failed OS process creation is not a full machine-level sandbox guarantee. Process isolation contains blocking client work; it does not revoke the trusted driver's filesystem/network privileges.

Only explicitly retryable provider failures with valid reported usage can retry. Schema errors, corrupt caches, unknown usage and timeouts do not trigger retries or an open-ended repair conversation. The driver must perform exactly one provider request per `complete` call, disable SDK-internal retries/batching, and report usage for failed attempts when available. Retrying belongs to this runtime.

Token counts arrive after the provider finishes, so the last attempted call can exceed the remaining token budget; its reported usage is retained and publication stops. This is a metered stop rule, not a guarantee against a single-call billing overrun. Configure provider-side limits separately if a hard spending cap is required. Defaults and all limits are replaceable in tests; negative, non-finite and invalid retry settings are rejected.

## Immutable, revalidated cache provenance

The default cache is under ignored `runs/model-cache/`. A key hashes cache-format version, purpose, provider/model, exact prompt version/content hash, schema version/hash, source payload hash, source ID, capture/message time, grounding-context digest where applicable and output-token setting. Format 2 stores that provenance, response digest, creation time, each reported attempt's original usage and their historical aggregate. Historical retries are not erased by retaining only the successful response's usage. Earlier formats are not relabeled or migrated automatically.

No pre-existing extraction cache was found in the inspected checkout. Historical-preservation tests seed an older prompt entry with fake-client provenance; no real historical records were fabricated or relabeled.

Both live and cached responses pass the same JSON schema and task-specific semantic validation. The code rebinds screenshot facts from the source artifact on replay. The cache's own schema, key, provenance, response digest, historical usage and timestamp are also validated. A corrupt/incompatible entry at an expected key is a fatal cache error; live mode does not silently repair, overwrite or reprice it.

Cache writes use exclusive creation. Prompt/schema/input changes create different keys and leave all older entries untouched, including their old prompt hash, model, creation time and historical usage. There is no automatic legacy migration, relabeling or fallback from a new prompt to an older response. Keep versioned prompt files immutable and introduce a new version when changing instructions. Even an accidental edit under the same version changes the content hash and prevents reuse.

Caches can contain fictional customer text transcribed from evidence. Keep them local and out of submission archives, and protect them as source data. Hashes detect corruption and binding mismatches but do not authenticate a maliciously rewritten cache cryptographically. Exact schema/semantic checks still apply to every entry. Cache creation time is processing provenance, not an evidence observation time, and does not backdate source facts.

## Actual usage and privacy

Every attempted live call is counted before execution. Reported input/output tokens and optional provider-reported cost in integer micro-USD are metered before response validation, so malformed responses and failed retry attempts are not treated as free. Missing usage stops the run, increments `unmetered_attempts`, marks `usage_complete=false` and leaves cost unknown. Timeouts cannot be assumed unbilled. Provider/model identity must match the configured profile; mismatches abort and mark attribution incomplete.

Cache hits count as adapter invocations but have zero new provider calls/tokens. Original usage remains separately labeled by `cache_historical_*` fields, including creation attempts, input/output tokens and reported cost; it is not relabeled as a new call, erased or charged again. The same cache key contributes historical creation totals only once per run, even if replayed repeatedly. Unknown costs remain null rather than fabricated estimates. Actual costs are not independently verified against a provider invoice.

The coordinator attaches `inference_usage` to its aggregate run summary on success and failure. It contains only configured provider/model names, numeric counters, completeness flags and cost/unknown markers. No messages, screenshot text, source IDs, cache keys, credentials, raw responses, plugin names or exception strings are logged. Worker console output is suppressed. A trusted driver's separate file/log handlers remain its responsibility.

The compatibility `external_calls` tool counter counts extraction adapter invocations and is not a billing counter. Use `inference_usage.model_calls` and reported token totals. Final submission reporting must still summarize the actual final run that produced `output.csv`; test-client counters are not hosted inference costs.

## Verification and limits

The full suite has 103 passing tests; model tests use fake clients only. It includes malformed/duplicate/extra-field responses, invented identifiers/citations/commands, corrupt and semantically invalid caches, cache response-size enforcement, prompt-version preservation, changed hashes/times, live opt-in, invocation/call/token/deadline exhaustion, bounded retries, missing usage, provider identity mismatch, actual worker termination, both adapters in the real pipeline, and a CLI worker round-trip followed by offline replay.

The deterministic three-case fixture remains byte-identical to its pre-model baseline. Native SQL/log/PDF adapters and offline Windows OCR now handle the supplied formats; models are not used for those text formats. Local OCR is deterministic extraction and does not consume provider tokens. It runs with a 30-second subprocess timeout per image and bounded returned bytes, but does not prove complete visual interpretation. Subject-scoped media gaps and missing policy proof stop publication. No completed 518-row submission or real hosted-model usage is claimed. See [evaluation/iteration_report.md](evaluation/iteration_report.md) for measured regressions. Remaining evidence/state correctness limits in [EVIDENCE_REASONING.md](EVIDENCE_REASONING.md) still apply.
