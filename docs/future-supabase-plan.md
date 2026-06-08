# Future Supabase Plan

Supabase is intentionally not implemented.

Metadata tables map directly to Supabase Postgres: users, datasets, columns, profiles, analytics questions, generated SQL, approvals, models, reports, evals, audit logs, and metrics.

Future migration options:
- Replace local JWT with Supabase Auth.
- Replace local upload paths with Supabase Storage.
- Keep DuckDB for local analytics or replace execution with warehouse queries.
- Move audit and approval tables unchanged.

Checklist: design RLS policies, map roles to claims, migrate files, rotate secrets, validate SQL governance, and update CI for Supabase tests.
