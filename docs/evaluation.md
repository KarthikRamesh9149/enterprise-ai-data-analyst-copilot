# Evaluation

The evaluation runner uses deterministic cases for intent classification and SQL safety. It stores evaluation runs and cases with pass/fail metrics.

Run locally with `make evals` or `POST /evals/run` as admin. Interpret pass rate as a local regression signal, not an external model benchmark.
