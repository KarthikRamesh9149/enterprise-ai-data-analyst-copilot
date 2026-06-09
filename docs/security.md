# Security

This project treats security and governance as core product requirements, especially around AI-generated SQL.

## Implemented Controls

| Area | Control |
| --- | --- |
| Authentication | JWT login flow with bcrypt password hashing |
| Authorization | Role-based access control for admin, analyst, reviewer, and viewer users |
| Data ownership | Dataset access checks for owner-scoped workflows |
| Uploads | CSV-only upload path, size limits, safe filenames, parser cleanup |
| SQL safety | Read-only `SELECT`/`WITH` allowlist, blocked dangerous DuckDB features, unknown identifier detection |
| Sensitive data | Sensitive-column pattern detection and wildcard projection blocking |
| Human approval | Generated SQL requires reviewer/admin approval before execution |
| Auditing | Key actions are recorded as audit events |
| Secrets | `.env`, logs, local databases, uploads, and generated reports are ignored |
| Local demos | Mock providers keep tests and demos deterministic without API keys |

## SQL Threat Model

Generated SQL is considered untrusted input. The validator blocks:

- DDL and DML.
- Multiple statements.
- External file reads.
- `COPY`, `ATTACH`, `INSTALL`, `LOAD`, and `PRAGMA`.
- Unknown tables or columns.
- Sensitive column references.
- `SELECT *` when sensitive-pattern columns exist.

The approval gate exists because static validation alone is not enough for enterprise analytics. Human review gives the project a concrete governance workflow that can be inspected during technical review.

## Local-Only Limitations

- Demo passwords are intentionally public.
- The default JWT secret must be changed outside local development.
- Rate limiting can fall back to process memory.
- Local filesystem storage is not production object storage.
- This project does not implement SSO, RLS, tenant isolation, SIEM forwarding, or production incident response.

## Production Hardening Checklist

- Move secrets into a managed secrets service.
- Use managed identity or SSO.
- Add tenant isolation and row-level security.
- Store uploads and reports in object storage.
- Add centralized audit retention.
- Add structured tracing, metrics, and alerts.
- Expand adversarial SQL and prompt-injection tests.
- Add dependency scanning and container scanning to CI.
