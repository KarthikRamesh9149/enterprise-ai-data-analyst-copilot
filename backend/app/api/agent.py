from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.workflow import run_agent
from app.api.datasets import get_dataset_or_404
from app.api.deps import current_user
from app.db.models import AgentRun, AgentTrace, User
from app.db.session import get_db
from app.schemas.requests import AgentRunRequest

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run")
def run(payload: AgentRunRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, payload.dataset_id, user) if payload.dataset_id else None
    agent_run = run_agent(db, user.id, payload.question, dataset)
    db.commit()
    return agent_run


@router.get("/runs")
def runs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(AgentRun).order_by(AgentRun.created_at.desc())
    if user.role != "admin":
        query = query.filter(AgentRun.user_id == user.id)
    return query.limit(100).all()


@router.get("/runs/{run_id}")
def get_run(run_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    run = db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if user.role != "admin" and run.user_id != user.id:
        raise HTTPException(status_code=403, detail="Run access denied")
    return run


@router.get("/runs/{run_id}/trace")
def trace(run_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    run = db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if user.role != "admin" and run.user_id != user.id:
        raise HTTPException(status_code=403, detail="Run access denied")
    return db.query(AgentTrace).filter(AgentTrace.agent_run_id == run_id).order_by(AgentTrace.created_at).all()
