from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.models import Approval, Dataset, GeneratedSQLQuery, User
from app.db.session import get_db
from app.schemas.requests import ApprovalReviewRequest
from app.services.audit import audit
from app.services.sql import SQLSafetyError, bind_approval

router = APIRouter(prefix="/approvals", tags=["approvals"])


def sql_approval_scope(approval: Approval, db: Session) -> tuple[GeneratedSQLQuery, Dataset]:
    query = db.get(GeneratedSQLQuery, approval.resource_id)
    dataset = db.get(Dataset, query.dataset_id) if query else None
    if (
        not query
        or not dataset
        or approval.requested_by != query.user_id
        or dataset.uploaded_by != query.user_id
    ):
        raise HTTPException(status_code=403, detail="Approval resource ownership mismatch")
    return query, dataset


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
    query: GeneratedSQLQuery | None = None
    dataset: Dataset | None = None
    if approval.resource_type == "generated_sql_query":
        query, dataset = sql_approval_scope(approval, db)
        if query.safety_status != "safe":
            raise HTTPException(status_code=400, detail="Unsafe or missing SQL cannot be approved")
    approval.status = "approved"
    approval.approved_by = user.id
    approval.reviewed_at = datetime.utcnow()
    approval.reviewer_notes = payload.reviewer_notes
    if query and dataset:
        try:
            bind_approval(query, dataset)
        except SQLSafetyError as exc:
            raise HTTPException(status_code=400, detail={"message": "SQL failed safety validation", "findings": exc.findings}) from exc
        query.approved_at = datetime.utcnow()
    audit(db, user.id, "approval.approve", approval.resource_type, str(approval.resource_id))
    db.commit()
    return approval


@router.post("/{approval_id}/reject")
def reject(approval_id: UUID, payload: ApprovalReviewRequest, user: User = Depends(require_permission("approvals:review")), db: Session = Depends(get_db)):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.resource_type == "generated_sql_query":
        sql_approval_scope(approval, db)
    approval.status = "rejected"
    approval.approved_by = user.id
    approval.reviewed_at = datetime.utcnow()
    approval.reviewer_notes = payload.reviewer_notes
    audit(db, user.id, "approval.reject", approval.resource_type, str(approval.resource_id))
    db.commit()
    return approval
