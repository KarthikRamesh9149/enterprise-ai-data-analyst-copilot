from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.datasets import get_dataset_or_404
from app.api.deps import current_user, require_permission
from app.db.models import ForecastRun, User
from app.db.session import get_db
from app.ml.forecasting import run_revenue_forecast
from app.schemas.requests import ForecastRequest
from app.services.audit import audit

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


@router.post("/revenue/run")
def revenue(payload: ForecastRequest, user: User = Depends(require_permission("forecasts:run")), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, payload.dataset_id, user, write=True)
    run = run_revenue_forecast(db, dataset, user.id, payload.forecast_target, payload.horizon_months)
    audit(db, user.id, "forecast.run", "forecast_run", str(run.id), {"target": payload.forecast_target})
    db.commit()
    return run


@router.get("/runs")
def runs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(ForecastRun).order_by(ForecastRun.created_at.desc())
    if user.role != "admin":
        query = query.filter(ForecastRun.created_by == user.id)
    return query.all()


@router.get("/runs/{forecast_id}")
def get_run(forecast_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    run = db.get(ForecastRun, forecast_id)
    if not run:
        raise HTTPException(status_code=404, detail="Forecast not found")
    if user.role != "admin" and run.created_by != user.id:
        raise HTTPException(status_code=403, detail="Forecast access denied")
    return run
