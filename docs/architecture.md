# Architecture

The system is a local-first enterprise analytics SaaS. It is designed to demonstrate a realistic internal AI product rather than a notebook or prompt-only prototype.

## System Layers

| Layer | Responsibility |
| --- | --- |
| Next.js frontend | Role-aware SaaS UI for datasets, analytics, modeling, forecasting, reports, approvals, evals, and admin |
| FastAPI backend | Product APIs, auth dependencies, orchestration, validation, and service boundaries |
| PostgreSQL metadata | Users, datasets, schema metadata, generated SQL, approvals, results, reports, evals, and audit logs |
| DuckDB analytics | Local execution engine for approved analytical SQL over uploaded CSV data |
| AI workflow | Intent classification, schema-aware SQL generation, validation, approval routing, and trace persistence |
| ML workflow | Churn modeling, risk scoring, forecasting, MLflow run tracking, and model cards |
| Local storage | Uploaded CSV files and generated report artifacts |
| Redis/cache layer | Local cache and rate-limit support |

## Backend Boundaries

The backend is split into:

- `api/`: FastAPI routers and request-level authorization.
- `services/`: dataset, SQL, report, audit, rate-limit, and provider logic.
- `agents/`: LangGraph-style analyst workflow.
- `ml/`: churn and forecasting workflows.
- `evals/`: deterministic evaluation runner.
- `db/`: SQLAlchemy models and database session setup.
- `scripts/`: seed, smoke, and evaluation entrypoints.

## Frontend Boundaries

The frontend is organized around product workflows:

- Dashboard overview.
- Dataset upload, validation, schema, profile, and sample views.
- Governed natural-language analytics.
- SQL approval and execution.
- Churn modeling and risk scores.
- Revenue forecasting.
- Executive reports.
- Evaluation and admin observability.

## AI Governance Flow

```text
Business question
  -> intent classification
  -> schema inspection
  -> provider SQL candidate
  -> SQL safety validator
  -> persisted query record
  -> reviewer/admin approval
  -> DuckDB execution
  -> result preview and chart
  -> audit log
```

AI-generated SQL is not trusted by default. It must pass the validator and receive human approval before execution.

## Data Flow

1. A user uploads a CSV.
2. The backend stores the file locally and records metadata in PostgreSQL.
3. Validation/profile services infer schema and quality signals.
4. The dataset is loaded into DuckDB using a generated table name.
5. Natural-language questions generate SQL against that table.
6. Safe and approved SQL runs in DuckDB.
7. Result metadata, previews, charts, traces, and audit logs are persisted.

## Deployment Boundary

The current version is intentionally local-first. Production deployment would require managed secrets, object storage, SSO or managed auth, stronger tenant isolation, central observability, and infrastructure-as-code.
