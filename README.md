# HackerRank Orchestrate implementation

The intended project is in [`hackerrank-orchestrate-october26/`](hackerrank-orchestrate-october26/README.md).
HackerRank / InterviewStreet supplied the challenge and participant dataset; attribution and the original instructions are preserved there.

```powershell
cd hackerrank-orchestrate-october26
python -m pip install -r requirements.txt
python -B code/evaluation/main.py
python -B code/evaluation/sample_eval.py predict --run runs/my-sample-run
python -B code/evaluation/sample_eval.py compare --run runs/my-sample-run --report runs/my-sample-run/report.md
```

Use a new run directory for every prediction freeze. Public references are opened only by the separate comparison command. Target requests can be diagnosed with `predict --requests-file deletion_requests.csv --expected-cases 518`; these are not scored against public answers. The normal CLI (`python -B code/main.py`) publishes only after every request succeeds and validates. Partial diagnostic predictions are not a submission.

The original upload recorded the project directory as a Git link to the starter commit, omitting the local implementation. The repository repair tracks the actual project files without deleting the local nested Git checkout. `.implementation/` contains historical staging files and is not used by the executable implementation.

This is a work in progress. See the project's evaluation reports for measured results and unresolved evidence requirements; a high public score from another implementation is not this implementation's measured accuracy.
