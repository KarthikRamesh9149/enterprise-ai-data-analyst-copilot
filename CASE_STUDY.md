# Portfolio Case Study

## Enterprise AI Data Analyst and Forecasting Copilot

This project is a local-first enterprise analytics product that demonstrates AI engineering, data science, analytics engineering, full-stack product development, and AI governance in one cohesive workflow.

The goal was to build the kind of internal tool a data, risk, or revenue operations team could use to move from a business question to governed analysis without giving an LLM direct execution authority.

## Problem

Business teams often need answers from messy customer and revenue data:

- Which customer segments have the highest churn?
- Which accounts are most at risk?
- What revenue might look like next quarter?
- Which model outputs can be trusted?
- Who approved an AI-generated query before it ran?

The product addresses those questions while keeping the AI path auditable, bounded, and reproducible.

## Product Outcome

The application supports a complete analyst workflow:

1. Upload synthetic customer or revenue CSV data.
2. Validate the dataset and inspect quality issues.
3. Profile schema, nulls, distributions, sample values, and warnings.
4. Ask a natural-language question.
5. Generate SQL through deterministic mock mode or optional OpenAI mode.
6. Validate SQL through a strict allowlist.
7. Require reviewer/admin approval before execution.
8. Execute approved SQL in DuckDB.
9. Show tables and Plotly chart specs.
10. Train churn models and produce risk scores.
11. Forecast revenue.
12. Generate executive reports.
13. Inspect evaluations, traces, audit logs, and observability screens.

## Architecture Decisions

| Decision | Rationale |
| --- | --- |
| FastAPI backend | Clear API boundaries, type-friendly service layer, strong local development loop |
| Next.js frontend | Reviewable SaaS product surface rather than a backend-only demo |
| PostgreSQL metadata | Realistic app state for users, datasets, approvals, queries, audits, and evals |
| DuckDB analytics | Fast local SQL execution over uploaded CSV data without external warehouse setup |
| SQL approval gate | AI-generated SQL is untrusted until validated and human-approved |
| Mock provider mode | Tests and demos are deterministic and do not require paid API access |
| Optional OpenAI provider | Shows production-oriented provider integration without making it mandatory |
| MLflow | Demonstrates experiment tracking and model governance awareness |
| Docker Compose | Reproducible local stack for technical review and walkthroughs |

## AI Governance Design

The most important design choice is that natural-language analytics does not directly execute generated SQL.

The AI path is:

```text
Question -> schema-aware prompt -> SQL candidate -> SQL validator -> approval queue -> DuckDB execution -> audit log
```

The validator blocks:

- DDL and DML.
- Multiple statements.
- External file access.
- DuckDB `COPY`, `ATTACH`, `INSTALL`, `LOAD`, and `PRAGMA`.
- Unknown tables or columns.
- Sensitive column patterns.
- Wildcard selection when sensitive columns exist.

This makes the project useful for discussing real enterprise AI systems where safety, governance, traceability, and human review matter as much as model output quality.

## Data Science Workflow

The ML path demonstrates practical, explainable workflows:

- Churn classification with scikit-learn.
- Numeric and categorical preprocessing.
- Accuracy, F1, and ROC AUC tracking.
- Feature importance extraction.
- Customer risk bands and recommended actions.
- Revenue forecasting workflow.
- MLflow run tracking.
- Model cards with limitations and monitoring notes.

## Evaluation and Quality

The project includes multiple quality gates:

- `ruff` for backend linting.
- `mypy` for backend type checking.
- `pytest` for product workflow coverage.
- Deterministic eval runner for intent and SQL safety checks.
- TypeScript type checking.
- Next.js production build.
- `npm audit`.
- Docker Compose config validation.
- Browser E2E smoke path against demo data.

## What This Demonstrates

This project is designed to signal:

- Ability to build beyond notebooks and prototypes.
- Understanding of enterprise AI risk controls.
- Full-stack implementation skill.
- Practical ML workflow knowledge.
- LLM provider integration with deterministic fallback.
- Clean local infrastructure and documentation.
- Product judgment around auditability, RBAC, and approval workflows.

## Production Hardening Roadmap

Before using this architecture in production, the next steps would be:

- Replace demo auth with managed identity or SSO.
- Move uploads and reports to object storage.
- Add tenant isolation and row-level security.
- Add persistent observability, tracing, and alerting.
- Add secrets management.
- Expand evaluation datasets and adversarial SQL tests.
- Add deployment IaC.
- Add stricter model monitoring and drift detection.
