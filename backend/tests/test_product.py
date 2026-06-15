from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth, churn_csv


def upload_dataset(client: TestClient, token: str) -> dict:
    response = client.post(
        "/datasets/upload",
        files={"file": ("customer_churn.csv", churn_csv(), "text/csv")},
        headers=auth(token),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_auth_register_login_me_and_invalid_password(client: TestClient):
    response = client.post("/auth/register", json={"email": "a@example.com", "password": "DemoPassword123!", "role": "analyst"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert response.json()["user"]["role"] == "viewer"
    assert client.get("/auth/me", headers=auth(token)).status_code == 200
    bad = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert bad.status_code == 401
    assert client.get("/datasets").status_code == 401


def test_rbac_viewer_cannot_upload_admin_can_access_audit(client: TestClient, tokens: dict):
    denied = client.post("/datasets/upload", files={"file": ("x.csv", b"a\n1\n", "text/csv")}, headers=auth(tokens["viewer"]))
    assert denied.status_code == 403
    assert client.get("/admin/audit-logs", headers=auth(tokens["analyst"])).status_code == 403
    assert client.get("/admin/audit-logs", headers=auth(tokens["admin"])).status_code == 200
    assert client.get("/approvals", headers=auth(tokens["reviewer"])).status_code == 200
    assert client.get("/approvals", headers=auth(tokens["viewer"])).status_code == 403


def test_dataset_upload_validate_profile_schema_sample_and_duckdb(client: TestClient, tokens: dict):
    dataset = upload_dataset(client, tokens["analyst"])
    dataset_id = dataset["id"]
    validation = client.post(f"/datasets/{dataset_id}/validate", headers=auth(tokens["analyst"]))
    assert validation.status_code == 200
    assert validation.json()["missing_required_columns"] == []
    assert client.get(f"/datasets/{dataset_id}/schema", headers=auth(tokens["analyst"])).json()
    assert client.get(f"/datasets/{dataset_id}/profile", headers=auth(tokens["analyst"])).status_code == 200
    assert len(client.get(f"/datasets/{dataset_id}/sample", headers=auth(tokens["analyst"])).json()) > 0
    loaded = client.post(f"/datasets/{dataset_id}/load-to-duckdb", headers=auth(tokens["analyst"]))
    assert loaded.status_code == 200
    assert loaded.json()["duckdb_table_name"].startswith("ds_customer_churn_")


def test_dataset_rejects_invalid_csv_and_missing_required_validation(client: TestClient, tokens: dict):
    invalid = client.post("/datasets/upload", files={"file": ("bad.txt", b"x", "text/plain")}, headers=auth(tokens["analyst"]))
    assert invalid.status_code == 400
    response = client.post("/datasets/upload", files={"file": ("small.csv", b"a,b\n1,2\n", "text/csv")}, headers=auth(tokens["analyst"]))
    assert response.status_code == 200
    validation = client.post(f"/datasets/{response.json()['id']}/validate", headers=auth(tokens["analyst"]))
    assert validation.json()["missing_required_columns"]


def test_sql_generation_validation_approval_execution_and_chart(client: TestClient, tokens: dict):
    dataset = upload_dataset(client, tokens["analyst"])
    dataset_id = dataset["id"]
    client.post(f"/datasets/{dataset_id}/load-to-duckdb", headers=auth(tokens["analyst"]))
    question = client.post(
        "/analytics/question",
        json={"dataset_id": dataset_id, "question": "Which customer segments have the highest churn rate?"},
        headers=auth(tokens["analyst"]),
    )
    assert question.status_code == 200, question.text
    query = question.json()["query"]
    assert query["safety_status"] == "safe"
    blocked = client.post("/analytics/validate-sql", json={"dataset_id": dataset_id, "sql": "DROP TABLE users"}, headers=auth(tokens["analyst"]))
    assert blocked.json()["status"] == "blocked"
    denied = client.post("/analytics/execute-sql", json={"query_id": query["id"]}, headers=auth(tokens["analyst"]))
    assert denied.status_code == 403
    approval = client.post("/analytics/approve-sql", json={"query_id": query["id"]}, headers=auth(tokens["reviewer"]))
    assert approval.status_code == 200
    executed = client.post("/analytics/execute-sql", json={"query_id": query["id"]}, headers=auth(tokens["analyst"]))
    assert executed.status_code == 200, executed.text
    assert executed.json()["row_count"] > 0
    assert client.get(f"/analytics/queries/{query['id']}/chart", headers=auth(tokens["analyst"])).json()["chart_type"] == "bar"


def test_approved_sql_is_revalidated_at_execution(client: TestClient, tokens: dict, db):
    dataset = upload_dataset(client, tokens["analyst"])
    dataset_id = dataset["id"]
    client.post(f"/datasets/{dataset_id}/load-to-duckdb", headers=auth(tokens["analyst"]))
    question = client.post(
        "/analytics/question",
        json={"dataset_id": dataset_id, "question": "Which customer segments have the highest churn rate?"},
        headers=auth(tokens["analyst"]),
    )
    query = question.json()["query"]
    assert client.post("/analytics/approve-sql", json={"query_id": query["id"]}, headers=auth(tokens["reviewer"])).status_code == 200

    from app.db.models import GeneratedSQLQuery

    stored = db.get(GeneratedSQLQuery, query["id"])
    stored.validated_sql = "DROP TABLE users"
    db.commit()

    executed = client.post("/analytics/execute-sql", json={"query_id": query["id"]}, headers=auth(tokens["analyst"]))

    assert executed.status_code == 400
    assert "SQL failed safety validation" in str(executed.json()["detail"])


def test_agent_modeling_forecasting_reports_evals_admin(client: TestClient, tokens: dict):
    dataset = upload_dataset(client, tokens["analyst"])
    dataset_id = dataset["id"]
    agent = client.post("/agent/run", json={"dataset_id": dataset_id, "question": "Why did churn increase?"}, headers=auth(tokens["analyst"]))
    assert agent.status_code == 200
    assert client.get(f"/agent/runs/{agent.json()['id']}/trace", headers=auth(tokens["analyst"])).json()
    model = client.post("/modeling/churn/train", json={"dataset_id": dataset_id, "target_column": "churned"}, headers=auth(tokens["analyst"]))
    assert model.status_code == 200, model.text
    assert model.json()["metrics"]
    assert client.get(f"/modeling/models/{model.json()['id']}/risk-scores", headers=auth(tokens["analyst"])).json()
    forecast = client.post("/forecasting/revenue/run", json={"dataset_id": dataset_id, "forecast_target": "total_revenue", "horizon_months": 3}, headers=auth(tokens["analyst"]))
    assert forecast.status_code == 200, forecast.text
    report = client.post("/reports/generate", json={"dataset_id": dataset_id, "title": "Executive Report"}, headers=auth(tokens["analyst"]))
    assert report.status_code == 200
    assert "Limitations" in report.json()["markdown_content"]
    evaluation = client.post("/evals/run", json={"name": "test-eval", "dataset_name": "demo"}, headers=auth(tokens["admin"]))
    assert evaluation.status_code == 200
    assert client.get("/evals/summary", headers=auth(tokens["admin"])).json()["cases"] >= 4
    assert client.get("/admin/analytics", headers=auth(tokens["admin"])).json()["datasets"] >= 1
