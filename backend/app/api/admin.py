from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.models import AuditLog, Dataset, GeneratedSQLQuery, MLModel, SystemMetric, User
from app.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs")
def audit_logs(user: User = Depends(require_permission("admin:read")), db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()


@router.get("/analytics")
def analytics(user: User = Depends(require_permission("admin:read")), db: Session = Depends(get_db)):
    return {
        "users": db.query(func.count(User.id)).scalar(),
        "datasets": db.query(func.count(Dataset.id)).scalar(),
        "queries": db.query(func.count(GeneratedSQLQuery.id)).scalar(),
        "models": db.query(func.count(MLModel.id)).scalar(),
        "blocked_sql": db.query(func.count(GeneratedSQLQuery.id)).filter(GeneratedSQLQuery.safety_status == "blocked").scalar(),
    }


@router.get("/observability")
def observability(user: User = Depends(require_permission("admin:read")), db: Session = Depends(get_db)):
    metrics = db.query(SystemMetric).order_by(SystemMetric.created_at.desc()).limit(100).all()
    return {"metrics": metrics, "service": "local-fastapi", "status": "ok"}


@router.get("/users")
def users(user: User = Depends(require_permission("admin:read")), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/system-health")
def system_health(user: User = Depends(require_permission("admin:read")), db: Session = Depends(get_db)):
    return {"api": "ok", "database": "ok", "duckdb": "configured", "mlflow": "local"}
