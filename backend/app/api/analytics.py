from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.datasets import get_dataset_or_404
from app.api.deps import current_user, require_permission
from app.core.rbac import has_permission
from app.db.models import AnalyticsQuestion, Approval, Chart, GeneratedSQLQuery, SQLExecutionResult, User
from app.db.session import get_db
from app.schemas.requests import ApproveSQLRequest, ExecuteSQLRequest, QuestionRequest, ValidateSQLRequest
from app.services.audit import audit, metric
from app.services.rate_limit import rate_limit
from app.services.sql import SQLSafetyError, bind_approval, classify_intent, execute_query, generate_sql, validate_sql

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_query_for_user(db: Session, query_id: UUID, user: User) -> GeneratedSQLQuery:
    query = db.get(GeneratedSQLQuery, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    if user.role != "admin" and query.user_id != user.id:
        raise HTTPException(status_code=403, detail="Query access denied")
    return query


@router.post("/question", dependencies=[Depends(rate_limit("analytics"))])
def ask_question(payload: QuestionRequest, user: User = Depends(require_permission("analytics:ask")), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, payload.dataset_id, user)
    intent = classify_intent(payload.question)
    sql, explanation = generate_sql(payload.question, dataset)
    question = AnalyticsQuestion(user_id=user.id, dataset_id=dataset.id, question=payload.question, intent=intent)
    db.add(question)
    db.flush()
    columns = {c.column_name for c in dataset.columns}
    safety = validate_sql(sql, dataset, columns)
    query = GeneratedSQLQuery(
        question_id=question.id,
        user_id=user.id,
        dataset_id=dataset.id,
        generated_sql=sql,
        validated_sql=safety.validated_sql,
        explanation=explanation,
        safety_status=safety.status,
        safety_findings=safety.findings,
    )
    db.add(query)
    db.flush()
    db.add(
        Approval(
            requested_by=user.id,
            action_type="sql_execution",
            resource_type="generated_sql_query",
            resource_id=query.id,
            status="pending",
            request_reason=f"Execute approved analytics question: {payload.question}",
        )
    )
    audit(db, user.id, "analytics.question", "generated_sql_query", str(query.id), {"intent": intent, "safety": safety.status})
    db.commit()
    return {"question": question, "query": query}


@router.post("/validate-sql")
def validate_sql_endpoint(payload: ValidateSQLRequest, user: User = Depends(require_permission("analytics:ask")), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, payload.dataset_id, user)
    result = validate_sql(payload.sql, dataset, {c.column_name for c in dataset.columns})
    return result.__dict__


@router.post("/approve-sql")
def approve_sql(payload: ApproveSQLRequest, user: User = Depends(require_permission("sql:approve")), db: Session = Depends(get_db)):
    query = db.get(GeneratedSQLQuery, payload.query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    if query.safety_status != "safe":
        raise HTTPException(status_code=400, detail="Unsafe SQL cannot be approved")
    dataset = get_dataset_or_404(db, query.dataset_id, user)
    if dataset.uploaded_by != query.user_id:
        raise HTTPException(status_code=403, detail="Query and dataset ownership mismatch")
    approval = db.query(Approval).filter(Approval.resource_id == query.id, Approval.resource_type == "generated_sql_query").first()
    if not approval or approval.requested_by != query.user_id:
        raise HTTPException(status_code=403, detail="Approval resource ownership mismatch")
    try:
        bind_approval(query, dataset)
    except SQLSafetyError as exc:
        raise HTTPException(status_code=400, detail={"message": "SQL failed safety validation", "findings": exc.findings}) from exc
    query.approved_at = datetime.utcnow()
    approval.status = "approved"
    approval.approved_by = user.id
    approval.reviewed_at = datetime.utcnow()
    approval.reviewer_notes = payload.reviewer_notes
    audit(db, user.id, "sql.approve", "generated_sql_query", str(query.id))
    db.commit()
    return query


@router.post("/execute-sql", dependencies=[Depends(rate_limit("execute_sql"))])
def execute_sql(payload: ExecuteSQLRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.get(GeneratedSQLQuery, payload.query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    if query.approval_status != "approved":
        raise HTTPException(status_code=403, detail="SQL must be approved before execution")
    if not (has_permission(user.role, "sql:execute") or has_permission(user.role, "sql:execute:approved")):
        audit(db, user.id, "sql.execute_denied", "generated_sql_query", str(query.id), {"reason": "permission"})
        db.commit()
        raise HTTPException(status_code=403, detail="Insufficient permission")
    if user.role != "admin" and query.user_id != user.id:
        audit(db, user.id, "sql.execute_denied", "generated_sql_query", str(query.id), {"reason": "owner"})
        db.commit()
        raise HTTPException(status_code=403, detail="Cannot execute another user's query")
    dataset = get_dataset_or_404(db, query.dataset_id, user)
    try:
        result = execute_query(db, query, dataset)
    except SQLSafetyError as exc:
        audit(db, user.id, "sql.execute_denied", "generated_sql_query", str(query.id), {"reason": "safety", "findings": exc.findings})
        db.commit()
        raise HTTPException(status_code=400, detail={"message": "SQL failed safety validation", "findings": exc.findings}) from exc
    audit(db, user.id, "sql.execute", "generated_sql_query", str(query.id), {"rows": result.row_count})
    metric(db, "sql.execution.latency_ms", result.latency_ms, {"query_id": str(query.id)})
    db.commit()
    return result


@router.get("/history")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(GeneratedSQLQuery).order_by(GeneratedSQLQuery.created_at.desc())
    if user.role != "admin":
        query = query.filter(GeneratedSQLQuery.user_id == user.id)
    return query.limit(100).all()


@router.get("/queries/{query_id}")
def get_query(query_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return get_query_for_user(db, query_id, user)


@router.get("/queries/{query_id}/results")
def get_results(query_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_query_for_user(db, query_id, user)
    return db.query(SQLExecutionResult).filter(SQLExecutionResult.sql_query_id == query_id).order_by(SQLExecutionResult.created_at.desc()).first()


@router.get("/queries/{query_id}/chart")
def get_chart(query_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_query_for_user(db, query_id, user)
    return db.query(Chart).filter(Chart.sql_query_id == query_id).order_by(Chart.created_at.desc()).first()


@router.get("/queries/{query_id}/trace")
def query_trace(query_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_query_for_user(db, query_id, user)
    return {"query_id": query_id, "steps": ["question_created", "sql_generated", "sql_validated", "approval_required", "execution_gated"]}
