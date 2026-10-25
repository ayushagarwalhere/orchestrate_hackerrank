# Ghost Data Still Exists

An offline deletion-audit agent for the HackerRank Orchestrate challenge.

## Architecture

The entry point runs a bounded `AuditAgent` with explicit state transitions and typed, replaceable tool interfaces. It loads immutable requests, builds one shared evidence index, investigates ownership and state, compiles deterministic plans, validates the complete CSV and atomically publishes approved bytes.

Models are confined to structured screenshot facts and ambiguous request intent. They cannot execute tools or generate final remediation. Prompts treat document contents as untrusted data; schemas, cache validation and source provenance checks are enforced in code.

The output transaction detects changed candidates and preserves the previous CSV on failure. Aggregate traces contain stage outcomes, durations, declared effects and failure types. Detailed evidence is available through the optional ledger export.

See `code/ENGINEERING.md` for the state diagram, tool contracts, prompt boundaries, publication protocol, test strategy and known limitations.

## Setup

Use Python 3.10 or newer. Extract `code.zip` into a working directory, then place the supplied `dataset/` beside `code/`:

```text
working-directory/
  README.md
  requirements.txt
  code/
  dataset/
```

```text
python -m pip install -r requirements.txt
python -B code/main.py --no-llm --out output.csv --trace run_trace.json
python -B code/validate_output.py --output output.csv --data dataset
```

The default run uses the supplied participant inputs and the included validated screenshot-fact caches. It needs no API credentials or new model calls. The dataset is supplied separately and is deliberately excluded from the archive.

The generated `output.csv` has 518 data rows, sorted by the numeric suffix of `case_id`. Its exact columns are `case_id,deletion_status,steps_json`. Public samples are evaluated separately and are not appended to the submission CSV.

## Delivered files

- `code.zip`: source, prompts, cached extraction provenance, tests and evaluation reports.
- `README.md`: these setup and run instructions.
- `log.txt`: the maintained project conversation log.
- `output.csv`: the validated prediction file.
- `outputs.csv`: an identical copy supplied under the requested plural filename.
- `release_manifest.json`: the pushed source commit, file hashes and release verification results.

The prediction CSV and conversation log are separate from the code archive. Submission artifacts are kept local and are excluded from Git.

## Optional diagnostics and tests

```text
python -B code/main.py --no-llm --out output.csv --ledger evidence_ledger.json
python -B code/evaluation/score.py
python -m pip install -r code/requirements-dev.txt
python -m pytest code/benchmark_tests -q
python -B code/evaluation/proof_tests.py
```

`score.py` reads public reference answers only during evaluation. The prediction entry point does not read them. The default coordinator builds one shared evidence index, reconstructs states, compiles ordered plans, validates a temporary CSV and publishes it atomically. Extraction or unresolved-intent failures stop publication.

An independent conservative implementation is preserved at `code/proof_main.py`. It has different evidence requirements and may stop where the default profile produces a result; it is not the default entry point.

## Documentation and limitations

Architecture and evidence handling are documented in `code/ARCHITECTURE.md` and `code/REQUEST_LEDGER.md`. Local evaluation, custom cases, failures and inference usage are recorded in `code/evaluation/evaluation_report.md` and `code/evaluation/usage_report.md`.

The default profile retains documented timing, naming, tie-breaking and retrospective-linking assumptions. Three public sample discrepancies remain unresolved. No hidden evaluation result is asserted. Historical cached extraction retains its original provenance and is not represented as newly generated evidence.

Challenge instructions and participant data are supplied by HackerRank / InterviewStreet. Existing source provenance documentation is included in `code/UPSTREAM.md` and `code/CHANGES.md`.
