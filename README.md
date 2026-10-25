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

The default CLI is the production coordinator. The independent, more conservative coordinator remains available through `code/proof_main.py`; its diagnostic evaluator is `code/evaluation/sample_eval.py`. Public references are read only during evaluation, not prediction. Architecture, provenance and limitations are documented in the project reports.

The original upload recorded the project directory as a Git link to the starter commit, omitting the local implementation. The repository repair tracks the actual project files without deleting the local nested Git checkout. `.implementation/` contains historical staging files and is not used by the executable implementation.

This is a work in progress. See the project's evaluation reports for local diagnostics and unresolved evidence requirements; they are not hosted or hidden evaluation results.
