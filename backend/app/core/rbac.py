from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    admin = "admin"
    analyst = "analyst"
    reviewer = "reviewer"
    viewer = "viewer"


PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "datasets:upload",
        "datasets:delete:any",
        "datasets:validate",
        "analytics:ask",
        "sql:approve",
        "sql:execute",
        "models:train",
        "forecasts:run",
        "reports:generate",
        "approvals:review",
        "evals:run",
        "admin:read",
    },
    "analyst": {
        "datasets:upload",
        "datasets:delete:own",
        "datasets:validate",
        "analytics:ask",
        "sql:execute:approved",
        "models:train",
        "forecasts:run",
        "reports:generate",
    },
    "reviewer": {
        "analytics:ask",
        "sql:approve",
        "approvals:review",
        "reports:read",
    },
    "viewer": {
        "analytics:ask",
        "reports:read",
    },
}


def has_permission(role: str, permission: str) -> bool:
    role_permissions = PERMISSIONS.get(role, set())
    return permission in role_permissions or permission.split(":")[0] + ":*" in role_permissions
