from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import AuditLog, SystemMetric


def audit(
    db: Session,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    event_metadata: dict | None = None,
    context: dict | None = None,
) -> None:
    context = context or {}
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            event_metadata=event_metadata or {},
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
        )
    )


def metric(db: Session, name: str, value: float, dimensions: dict | None = None) -> None:
    db.add(SystemMetric(metric_name=name, metric_value=value, dimensions=dimensions or {}))
