# Future Deployment Plan

Deployment is intentionally not implemented.

Suggested production plan: managed Postgres, managed Redis, object storage for uploads/reports, hosted MLflow or experiment tracking alternative, separately deployed FastAPI backend and Next.js frontend, TLS, real secrets management, error monitoring, log retention, backup/restore, and stricter rate limits.

Before public deployment: change JWT secret, remove demo passwords, add production CORS, enforce upload malware scanning, review RBAC, enable HTTPS-only cookies if switching auth transport, configure audit retention, and run security tests.
