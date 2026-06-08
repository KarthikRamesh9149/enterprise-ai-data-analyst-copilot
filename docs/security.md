# Security

Security controls include JWT auth, password hashing, RBAC, upload extension and size checks, safe filenames, path-confined storage, rate limiting, SQL allowlist validation, sensitive-column blocking, approval gates, safe API errors, CORS configuration, no committed secrets, and audit logs.

Local-only limitations: demo passwords are intentionally public, JWT secret must be changed for non-local use, and rate limiting falls back to process memory.
