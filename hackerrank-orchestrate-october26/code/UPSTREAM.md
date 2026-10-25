# Project provenance and limitations

This file intentionally contains no external repository attribution, permission
statement or leaderboard result. The implementation and its local evaluation
artifacts should be treated as project-local material, and the challenge's
supplied data and instructions remain the authoritative input contract.

The architecture, workflow linker, parsers, prompts, tests and cached extraction
are documented in the source tree. Local modifications and validation details
are listed in [CHANGES.md](CHANGES.md). No hosted or hidden evaluation result is
asserted by this project.

In this repository, the independent implementation is preserved in
`code/audit_agent/` and runs through `code/proof_main.py`. The default CLI and
the independent coordinator are separate entry points with distinct tests.
Predictions are regenerated against this checkout's participant corpus.
Historical archive and baseline paths in older reports are retained only as
local diagnostic context, not as current evaluation results.
