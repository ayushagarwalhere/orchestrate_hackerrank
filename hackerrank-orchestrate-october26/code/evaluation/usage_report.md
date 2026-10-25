# Inference usage status — 25 October 2026

No final full-dataset run producing root output.csv has completed. This report separates unsuccessful historical smoke testing, current public-sample diagnostics and fake-client tests from a future final submission run.

## Current public-sample inference

The frozen final sample run has 32 requests, six produced diagnostic rows and 26 failures. All 94 supplied artifacts passed the format parsers; semantic/policy coverage remains incomplete. JSON, logs and bounded in-memory SQL use deterministic parsing; PDF text uses pypdf and PNG text uses local Windows WinRT OCR. No model provider was configured, and no provider credentials or hosted inference were used.

| Provider/model | Adapter/model calls | Input tokens | Output tokens | Total tokens | Average tokens per sample request | Inference charges |
|---|---:|---:|---:|---:|---:|---:|
| None configured | 0 / 0 | 0 | 0 | 0 | 0/32 = 0 | 0 hosted inference charges |
| Overall | 0 / 0 | 0 | 0 | 0 | 0 | 0 hosted inference charges |

Historical cache creation calls/tokens/cost are zero for these model-free sample runs; no cache was reused or relabeled. Local OCR/CPU consumption and development-assistant usage are not included in provider token/cost totals. Those development costs have not been measured by this runtime. Sample prediction CSV SHA-256: `f97f6e6d396271e1e955e874f81c1fd808559892bb348a925922ae3ab4b0b574`. This partial diagnostic artifact is not a final submission.

## Earlier full-dataset smoke and tests

The earlier coordinator smoke loaded all 518 requests and stopped on unsupported extraction before indexing/publication; it made zero hosted calls and sent zero input/output tokens. Native adapters now replace that format-level blocker, but no completed 518-row output or final-run average/cost exists.

All 103 tests pass. Model/cache tests use fake clients; fake usage values test metering behavior and are not real inference charges. CLI fake-client tests include cache replay. The `external_calls` compatibility counter measures extraction adapter invocations, not billing; actual model accounting is in `inference_usage`.

## Runtime accounting and final-run requirements

`ModelRuntime` records invocation counts, attempted calls and retries, actual reported input/output tokens, optional provider-reported micro-USD cost and completeness flags. It meters reported usage before response validation. Missing usage and timeouts are explicitly unmetered with unknown cost, never assumed free. Provider/model mismatches mark attribution incomplete. Drivers must disable internal retries/batching and perform one provider request per attempt.

Validated cache hits consume no new provider calls/tokens and preserve original prompt/model/source/creation provenance and historical usage separately. Version/hash changes create new keys; no older cache is overwritten or relabeled. Aggregate usage is attached to run summaries without customer text or credentials. See [../MODEL_EXECUTION.md](../MODEL_EXECUTION.md).

Before submission, record the actual final run's provider/model names, calls including preprocessing/retries, input/output/total tokens, overall and per-model totals, averages over all 518 requests, cache usage, dated pricing/cost basis, total and per-request cost, and final input/output digests. No successful final run is claimed by replacing those measurements with sample or fake-client totals.
