# Current reproduction usage

The final default CLI generated all 518 validated rows in offline mode. New provider/model invocations: **0**; new input/output tokens: **0 / 0**; new hosted cost: **$0**, averaging **0 tokens and $0 per target request**. No provider/model was invoked in this reproduction. Historical screenshot facts retain their recorded model, prompt and extraction provenance; this does not claim that their original creation cost was zero. Local OCR/CPU and development-assistant usage are outside these provider totals and were not metered here.

Output SHA-256: e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc. Test clients use synthetic usage and are not real provider charges. The preserved independent profile's partial diagnostic CSV is not this final default output.

## Historical usage record from the transferred profile

# Usage report — current candidate

This report covers the full run producing 518-row output.csv with SHA-256 `e2055a0589327e563eb2cfddac20eeef1a4694c2b06a956ff1f94bc2dcfd92bc`.

| Runtime provider/model | Calls | Input tokens | Output tokens | Total | Per request | API cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| None invoked: offline replay | 0 | 0 | 0 | 0 | 0 | USD 0 |
| Total current runtime | 0 | 0 | 0 | 0 | 0 | USD 0 |

Live inference requires explicit --live-llm; this run used --no-llm. Model extraction was performed previously by the upstream author and is reused with permission. Imported cache counters below are author-recorded historical generation usage, not new calls or tokens spent during this run.

| Cached provider/model/task | Recorded calls | Recorded input | Recorded output | Recorded total |
| --- | ---: | ---: | ---: | ---: |
| google / gemini-4-argon / image_facts | 11 | 22576 | 3943 | 26519 |

All eleven image-fact files are bound to source SHA-256. Changed source images fail validation rather than silently reusing stale facts. No copied prediction CSV was used to produce the candidate. Historical extraction cost is not independently verified; the author's earlier price assumptions are not represented as current official rates. This replay has zero marginal API cost; it does not mean development was free.
Local development harness/provider: OpenAI Codex Desktop, runtime gpt-6.1-sol. Development tokens/cost are not separately available and are not fabricated.
