# Guide to the actual development record

This is an editorial navigation guide, compiled after implementation. It is not
a verbatim conversation, a replacement transcript, or a claim that these prompts
were written earlier in a different form. The separately uploaded root `log.txt`
preserves the recorded prompts and summaries, including failed iterations and
the switch to an author-approved baseline. The original author's implementation
is credited in `UPSTREAM.md`; only the listed local changes are attributed here.

| Review dimension | Actual user direction in log.txt | Result and qualification |
| --- | --- | --- |
| Ownership of evaluation decisions | “Report status accuracy separately from full-case exact accuracy.” | Separate status and full-case metrics, an all-32 comparison and explicit mismatch details. Tests passing are not presented as proof of hidden accuracy. |
| Precise technical instructions | “For every unresolved decision, report the candidate links or states, supporting and conflicting evidence IDs, and what specifically remains unknown.” | Investigation reports preserve uncertainty and alternative links. The later scoring profile retains disclosed inference assumptions; they are not retroactively described as proven evidence. |
| Iteration and correction | “Group failures by root cause and fix the largest supported category first.” | Earlier strict iterations and regressions remain in the log. The final baseline was reproduced before applying measured local changes, rather than claiming the earlier implementation achieved the later results. |
| Verification | “Add regression cases for those actual failures, and keep expected sample answers out of prediction logic.” | Prediction runs precede reference access; schema, time, cache, budget, SQL and publication failures have regression coverage. Packaged code is executed after extraction and compared by SHA-256. |
| Permission and authorship | “author is my friend and permits the use - and also this exact solution is behind 28.2” | Private reuse permission is recorded, attribution retained and the baseline independently regenerated. No claim of independent authorship of inherited modules or organizer approval is made. |
| Safety awareness | “Do not invent resource IDs, evidence references, ownership links, or restore permissions.” | This directed the earlier strict engine. The later explicit adoption of a heuristic baseline changed the tradeoff; inherited naming/timing/ownership assumptions remain disclosed. The current pass adds runtime boundaries without erasing that history. |

The current request asks to make agent architecture, prompt/tool design,
robustness and code readability visible. This produced real coordinator and tool
modules, versioned prompts, bounded model calls, validated cache reads, confined
SQL/manifest access, execution telemetry and atomic output publication. It also
requested changing past prompts; that portion was declined. The actual request
and this response are appended to the transcript unchanged in substance.

For interview preparation, explain the fixed workflow and why deterministic
planning follows model extraction. Demonstrate a rejected candidate preserving
the previous CSV, a corrupted cache being rejected, and the packaged run matching
the CSV hash. Discuss the remaining ownership and policy assumptions candidly.
