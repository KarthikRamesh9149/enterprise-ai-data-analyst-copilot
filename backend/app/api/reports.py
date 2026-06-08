from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.datasets import get_dataset_or_404
from app.api.deps import current_user, require_permission
from app.db.models import Report, User
from app.db.session import get_db
from app.schemas.requests import ReportRequest
from app.services.audit import audit
from app.services.rate_limit import rate_limit
from app.services.reports import generate_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", dependencies=[Depends(rate_limit("reports"))])
def generate(payload: ReportRequest, user: User = Depends(require_permission("reports:generate")), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, payload.dataset_id, user) if payload.dataset_id else None
    report = generate_report(db, user.id, payload.title, dataset, payload.agent_run_id)
    audit(db, user.id, "report.generate", "report", str(report.id))
    db.commit()
    return report


@router.get("")
def list_reports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(Report).order_by(Report.created_at.desc())
    if user.role not in {"admin", "reviewer"}:
        query = query.filter(Report.created_by == user.id)
    return query.all()


@router.get("/{report_id}")
def get_report(report_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if user.role not in {"admin", "reviewer"} and report.created_by != user.id:
        raise HTTPException(status_code=403, detail="Report access denied")
    return report


@router.get("/{report_id}/download")
def download(report_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report or not report.file_path or not Path(report.file_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    if user.role not in {"admin", "reviewer"} and report.created_by != user.id:
        raise HTTPException(status_code=403, detail="Report access denied")
    return FileResponse(report.file_path, filename=f"{report.title}.md")
