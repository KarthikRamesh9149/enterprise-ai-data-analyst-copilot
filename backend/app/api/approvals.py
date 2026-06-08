from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.models import Approval, GeneratedSQLQuery, User
from app.db.session import get_db
from app.schemas.requests import ApprovalReviewRequest
from app.services.audit import audit

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
def list_approvals(user: User = Depends(require_permission("approvals:review")), db: Session = Depends(get_db)):
    return db.query(Approval).order_by(Approval.created_at.desc()).all()


@router.get("/{approval_id}")
def get_approval(approval_id: UUID, user: User = Depends(require_permission("approvals:review")), db: Session = Depends(get_db)):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/approve")
def approve(approval_id: UUID, payload: ApprovalReviewRequest, user: User = Depends(require_permission("approvals:review")), db: Session = Depends(get_db)):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "approved"
    approval.approved_by = user.id
    approval.reviewed_at = datetime.utcnow()
    approval.reviewer_notes = payload.reviewer_notes
    if approval.resource_type == "generated_sql_query":
        query = db.get(GeneratedSQLQuery, approval.resource_id)
        if query and query.safety_status == "safe":
            query.approval_status = "approved"
            query.approved_at = datetime.utcnow()
    audit(db, user.id, "approval.approve", approval.resource_type, str(approval.resource_id))
    db.commit()
    return approval


@router.post("/{approval_id}/reject")
def reject(approval_id: UUID, payload: ApprovalReviewRequest, user: User = Depends(require_permission("approvals:review")), db: Session = Depends(get_db)):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "rejected"
    approval.approved_by = user.id
    approval.reviewed_at = datetime.utcnow()
    approval.reviewer_notes = payload.reviewer_notes
    audit(db, user.id, "approval.reject", approval.resource_type, str(approval.resource_id))
    db.commit()
    return approval
