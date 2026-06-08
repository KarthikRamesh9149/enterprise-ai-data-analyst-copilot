# API

All routes except `/health`, `/auth/register`, and `/auth/login` require JWT auth.

Health: `GET /health`.

Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.

Datasets: `POST /datasets/upload`, `GET /datasets`, `GET /datasets/{id}`, `DELETE /datasets/{id}`, `GET /datasets/{id}/schema`, `GET /datasets/{id}/profile`, `GET /datasets/{id}/sample`, `POST /datasets/{id}/validate`, `POST /datasets/{id}/load-to-duckdb`.

Analytics: `POST /analytics/question`, `POST /analytics/validate-sql`, `POST /analytics/approve-sql`, `POST /analytics/execute-sql`, `GET /analytics/history`, `GET /analytics/queries/{id}`, `GET /analytics/queries/{id}/results`, `GET /analytics/queries/{id}/chart`, `GET /analytics/queries/{id}/trace`.

Agent: `POST /agent/run`, `GET /agent/runs`, `GET /agent/runs/{id}`, `GET /agent/runs/{id}/trace`.

Modeling: `POST /modeling/churn/train`, `POST /modeling/churn/score`, `GET /modeling/models`, `GET /modeling/models/{id}`, metrics, feature importance, risk scores, and model cards routes.

Forecasting: `POST /forecasting/revenue/run`, `GET /forecasting/runs`, `GET /forecasting/runs/{id}`.

Reports: `POST /reports/generate`, `GET /reports`, `GET /reports/{id}`, `GET /reports/{id}/download`.

Approvals: `GET /approvals`, `GET /approvals/{id}`, `POST /approvals/{id}/approve`, `POST /approvals/{id}/reject`.

Evaluations: `POST /evals/run`, `GET /evals/runs`, `GET /evals/runs/{id}`, `GET /evals/runs/{id}/cases`, `GET /evals/summary`.

Admin: `GET /admin/audit-logs`, `GET /admin/analytics`, `GET /admin/observability`, `GET /admin/users`, `GET /admin/system-health`.
