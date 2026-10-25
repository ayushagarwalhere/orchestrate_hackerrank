# Authorized upstream and attribution

This solution is adapted from rsrsp21's Ghost Data Still Exists implementation:
https://github.com/rsrsp21/hackerrank-orchestrate-october26/tree/solution

Pinned upstream revision: `0c573f824adb5b4c0aef36a525d5dc424dc9f97d`.
The user states that the author is their friend, permits use of the solution,
and confirms this exact implementation produced 28.2/30 on the leaderboard.
This records that private permission; it does not assert a public open-source
license or organizer approval of entry eligibility. Original architecture,
workflow linker, parsers, prompts, tests and cached Gemini extraction are credited
to rsrsp21. Local modifications and their validation are listed in CHANGES.md.
The inherited baseline is not represented as independently authored here.

In this repository, the independent implementation is preserved in
`code/audit_agent/` and runs through `code/proof_main.py`. The default CLI uses
the authorized derivative transferred from the other local checkout at revision
`cc1b191`, plus its subsequent read-only forensic utility and tests. Its coordinator
is named `benchmark_agent.py` to avoid colliding with the independent package.
No upstream dataset, prediction CSV, credentials or conversation log was copied;
predictions are regenerated against this checkout's participant corpus. Historical
archive/baseline paths mentioned in older reports describe the earlier checkout,
not artifacts claimed to exist here.
