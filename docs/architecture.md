# Architecture

The app uses Next.js for the enterprise SaaS UI, FastAPI for product APIs, PostgreSQL for metadata, DuckDB for local analytics execution, MLflow for experiment tracking, Redis/in-memory rate limiting, and local filesystem storage for uploads/reports/artifacts.

Backend modules are split into API routers, services, ML workflows, LangGraph agent workflow, database models, and scripts. DuckDB tables are derived from uploaded CSVs and query execution is limited to approved safe SQL.

Frontend screens map to product domains: dashboard, datasets, analytics, modeling, forecasting, reports, approvals, evaluations, and admin.

The LangGraph workflow contains intent classification, schema inspection, planning, and critic nodes. Trace records are persisted for inspection.

Approval flow: question -> SQL generation -> SQL validation -> approval request -> reviewer/admin approval -> DuckDB execution -> result metadata/chart/audit log.
