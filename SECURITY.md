# Security Policy

## Supported Scope

This repository is a local-first portfolio project. Security work focuses on demonstrating enterprise AI controls and safe local operation.

## Security Controls Implemented

- JWT authentication.
- bcrypt password hashing.
- Role-based access control.
- Dataset ownership checks.
- CSV upload extension and size validation.
- Safe uploaded filenames.
- SQL allowlist validation.
- Sensitive-column detection.
- Human approval before SQL execution.
- Audit logging for key workflows.
- Deterministic mock AI providers for tests and demos.
- Ignored `.env`, local databases, logs, generated reports, and uploads.

## Secrets

Do not commit API keys, production secrets, local `.env` files, customer data, or exported databases.

If a secret is accidentally committed:

1. Revoke it immediately at the provider.
2. Rotate any dependent credentials.
3. Remove it from the repository history before public sharing.

## Reporting

For a portfolio review, open a GitHub issue with:

- Impact.
- Reproduction steps.
- Affected file or endpoint.
- Suggested remediation if known.

## Production Caveats

Before production use, this architecture would need managed secrets, SSO, tenant isolation, persistent monitoring, stricter audit retention, deployment hardening, object storage, and an expanded security test suite.

