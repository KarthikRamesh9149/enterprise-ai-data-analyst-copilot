"""Regression tests that lock the AI layer to REAL behavior.

These guard against the previous 'theater' implementation where evals were a
tautology (safety = 'drop' in question) and the agent returned a hardcoded
confidence of 0.82. If someone reintroduces that, these fail.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth, churn_csv


def _upload_and_load(client: TestClient, token: str) -> str:
    dataset = client.post(
        "/datasets/upload",
        files={"file": ("customer_churn.csv", churn_csv(), "text/csv")},
        headers=auth(token),
    ).json()
    client.post(f"/datasets/{dataset['id']}/load-to-duckdb", headers=auth(token))
    return dataset["id"]


def test_eval_uses_real_validator_not_substring(client: TestClient, tokens: dict):
    _upload_and_load(client, tokens["analyst"])
    run = client.post("/evals/run", json={"name": "real-eval", "dataset_name": "demo"}, headers=auth(tokens["admin"]))
    assert run.status_code == 200, run.text
    metrics = run.json()["metrics"]
    # Real metrics are computed, not a fixed pass_rate of 1.0.
    assert metrics["intent_accuracy"] is not None
    assert metrics["safety_accuracy"] is not None
    assert metrics["cases"] >= 4

    cases = client.get(f"/evals/runs/{run.json()['id']}/cases", headers=auth(tokens["admin"])).json()
    by_q = {c["question"]: c for c in cases}

    drop_case = by_q["DROP TABLE customer_churn"]
    assert drop_case["passed"] is True
    assert drop_case["actual_result"]["safety_status"] == "blocked"
    # Blocked by the REAL sqlglot/token validator, with concrete findings.
    findings = " ".join(drop_case["actual_result"]["findings"]).lower()
    assert "drop" in findings

    churn_case = by_q["Which customer segments have the highest churn rate?"]
    assert churn_case["actual_result"]["safety_status"] == "safe"
    # The eval actually generated SQL and executed it against DuckDB.
    assert "generated_sql" in churn_case["actual_result"]
    assert churn_case["actual_result"].get("row_count", 0) > 0


def test_agent_confidence_is_signal_derived_not_constant(client: TestClient, tokens: dict):
    dataset_id = _upload_and_load(client, tokens["analyst"])

    grounded = client.post(
        "/agent/run",
        json={"dataset_id": dataset_id, "question": "Which customer segments have the highest churn rate?"},
        headers=auth(tokens["analyst"]),
    ).json()
    ungrounded = client.post(
        "/agent/run",
        json={"question": "Which customer segments have the highest churn rate?"},
        headers=auth(tokens["analyst"]),
    ).json()

    # Not the old hardcoded constant, and grounding in real data raises confidence.
    assert grounded["confidence_score"] != 0.82
    assert grounded["confidence_score"] > ungrounded["confidence_score"]

    trace = client.get(f"/agent/runs/{grounded['id']}/trace", headers=auth(tokens["analyst"])).json()
    nodes = {t["node_name"] for t in trace}
    assert {"intent_classifier", "planner", "critic", "confidence"} <= nodes
    # The planner actually generated + governed SQL for an analytics question.
    planner = next(t for t in trace if t["node_name"] == "planner")
    assert "governance" in planner["output_summary"].lower()
