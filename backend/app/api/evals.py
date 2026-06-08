from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_permission
from app.db.models import EvaluationCase, EvaluationRun, User
from app.db.session import get_db
from app.evals.runner import run_evaluation
from app.schemas.requests import EvalRunRequest
from app.services.audit import audit

router = APIRouter(prefix="/evals", tags=["evals"])


@router.post("/run")
def run(payload: EvalRunRequest, user: User = Depends(require_permission("evals:run")), db: Session = Depends(get_db)):
    eval_run = run_evaluation(db, user.id, payload.name, payload.dataset_name)
    audit(db, user.id, "eval.run", "evaluation_run", str(eval_run.id), eval_run.metrics)
    db.commit()
    return eval_run


@router.get("/runs")
def runs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()


@router.get("/runs/{run_id}")
def get_run(run_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    run = db.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run


@router.get("/runs/{run_id}/cases")
def cases(run_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(EvaluationCase).filter(EvaluationCase.run_id == run_id).all()


@router.get("/summary")
def summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    total = db.query(func.count(EvaluationCase.id)).scalar() or 0
    passed = db.query(func.count(EvaluationCase.id)).filter(EvaluationCase.passed.is_(True)).scalar() or 0
    return {"cases": total, "passed": passed, "pass_rate": passed / total if total else 0}
