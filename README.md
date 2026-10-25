# HackerRank Orchestrate implementation

The intended project is in [`hackerrank-orchestrate-october26/`](hackerrank-orchestrate-october26/README.md).
HackerRank / InterviewStreet supplied the challenge and participant dataset; attribution and the original instructions are preserved there.

```powershell
cd hackerrank-orchestrate-october26
python -m pip install -r requirements.txt
python -B code/main.py --no-llm
python -B code/validate_output.py
python -B code/evaluation/score.py
```

The default CLI uses the authorized derivative that previously achieved 32/32 public statuses and 29/32 exact cases. The independent, more conservative coordinator remains available through `code/proof_main.py`; its diagnostic evaluator is `code/evaluation/sample_eval.py`. Public references are read only during evaluation, not prediction. Attribution and limitations are documented in the project's `code/UPSTREAM.md` and architecture/evaluation reports.

The original upload recorded the project directory as a Git link to the starter commit, omitting the local implementation. The repository repair tracks the actual project files without deleting the local nested Git checkout. `.implementation/` contains historical staging files and is not used by the executable implementation.

This is a work in progress. See the project's evaluation reports for measured results and unresolved evidence requirements; a high public score from another implementation is not this implementation's measured accuracy.
