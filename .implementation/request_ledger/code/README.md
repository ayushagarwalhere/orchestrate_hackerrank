# Ghost Data Still Exists

The implemented coordinator, tool contracts, model boundary and failure handling
are described in [ARCHITECTURE.md](ARCHITECTURE.md). A guide to the actual
development record is in [DECISION_GUIDE.md](evaluation/DECISION_GUIDE.md).

Place `code/` beside the supplied `dataset/`. Tested with Python 3.12.14 and
pdfplumber 0.11.9. The default run uses cached image facts and makes no live model calls.

```text
python -m pip install -r code/requirements.txt
python code/main.py --no-llm --trace run_trace.json
python code/main.py --no-llm --trace run_trace.json --ledger diagnostics/evidence-ledger.json
python code/validate_output.py
python code/evaluation/main.py
python code/evaluation/local_report.py
```

The root `output.csv` contains all 518 target requests. Local evaluation reports
describe generated rows, validation checks and known limitations. They are
diagnostic artifacts and are not claims about hosted or hidden evaluation.

The initial baseline was reproduced byte-for-byte with SHA-256
`0d80a7d4bad671870762bf5a6edab41a9c48d146dd2292367e5cb8b228207194`.
The candidate changes only three CSV evidence fields, replacing uncited COMPLETE
checks with eligible persistent account-absence evidence. See the evaluation report
for the affected rows, evidence scope and limitations.

```text
python -m pip install -r code/requirements-dev.txt
python -m pytest code/tests -q
python code/package.py
```

The source ZIP contains only `code/`, including this README, attribution, prompts,
cached extraction and evaluation reports. It excludes dataset/data, environments,
build caches, archives, and generated prediction backups. Upload the CSV and root
log.txt separately. No upload is performed by these commands.

Optional live extraction requires `requirements-live.txt`, provider credentials in
the environment, and explicit `--live-llm`. Current reproduction requires neither.
New live extraction uses the v3 fact prompt; imported v2 facts keep their original
provenance. The live model wrapper defaults to 32 adapter invocations. The agent
validates a staged candidate before atomic publication; failed validation leaves
the previous output untouched. A recorded aggregate trace is included under
`evaluation/agent_run_trace.json`.

Request interpretation and the shared evidence ledger are described in
[REQUEST_LEDGER.md](REQUEST_LEDGER.md). Unresolved authorization now blocks
publication. `--ledger` writes detailed source facts and per-file extraction
outcomes; unlike aggregate traces it may contain customer text and identifiers.
The measured results and remaining uncertainty for this change are in
[evaluation/request_ledger_report.md](evaluation/request_ledger_report.md).

## Inherited assumptions

The scoring profile jointly assigns workflows using timing and uses
numeric case-order tie breaks, a naming fallback, and retrospective ownership
membership. These are hypotheses, not direct ownership proof. State
citations are bounded by evidence/audit clocks; the local change also rejects
observations dated after their capture. Do not describe the scoring profile as
strictly excluding all future ownership information. The validator checks schema,
ordering, citations and time bounds; it does not prove inferred ownership or hidden
answer correctness. Unit tests and sample success are not leaderboard guarantees.
