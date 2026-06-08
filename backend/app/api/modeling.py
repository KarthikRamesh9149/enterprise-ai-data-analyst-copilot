from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.datasets import get_dataset_or_404
from app.api.deps import current_user, require_permission
from app.db.models import MLModel, ModelCard, RiskScore, User
from app.db.session import get_db
from app.ml.churn import train_churn_model
from app.schemas.requests import ChurnScoreRequest, ChurnTrainRequest
from app.services.audit import audit
from app.services.rate_limit import rate_limit

router = APIRouter(prefix="/modeling", tags=["modeling"])


@router.post("/churn/train", dependencies=[Depends(rate_limit("model_train"))])
def train(payload: ChurnTrainRequest, user: User = Depends(require_permission("models:train")), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, payload.dataset_id, user, write=True)
    model = train_churn_model(db, dataset, user.id, payload.target_column)
    audit(db, user.id, "model.train", "ml_model", str(model.id), {"metrics": model.metrics})
    db.commit()
    return model


@router.post("/churn/score")
def score(payload: ChurnScoreRequest, user: User = Depends(require_permission("models:train")), db: Session = Depends(get_db)):
    model = db.get(MLModel, payload.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if user.role != "admin" and model.created_by != user.id:
        raise HTTPException(status_code=403, detail="Model access denied")
    return db.query(RiskScore).filter(RiskScore.model_id == model.id).order_by(RiskScore.risk_probability.desc()).limit(100).all()


@router.get("/models")
def models(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(MLModel).order_by(MLModel.created_at.desc())
    if user.role != "admin":
        query = query.filter(MLModel.created_by == user.id)
    return query.all()


@router.get("/models/{model_id}")
def model(model_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(MLModel, model_id)
    if not item:
        raise HTTPException(status_code=404, detail="Model not found")
    if user.role != "admin" and item.created_by != user.id:
        raise HTTPException(status_code=403, detail="Model access denied")
    return item


@router.get("/models/{model_id}/metrics")
def metrics(model_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(MLModel, model_id)
    if item and user.role != "admin" and item.created_by != user.id:
        raise HTTPException(status_code=403, detail="Model access denied")
    return item.metrics if item else {}


@router.get("/models/{model_id}/feature-importance")
def feature_importance(model_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(MLModel, model_id)
    if item and user.role != "admin" and item.created_by != user.id:
        raise HTTPException(status_code=403, detail="Model access denied")
    return item.feature_importance if item else []


@router.get("/models/{model_id}/risk-scores")
def risk_scores(model_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    model = db.get(MLModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if user.role != "admin" and model.created_by != user.id:
        raise HTTPException(status_code=403, detail="Model access denied")
    return db.query(RiskScore).filter(RiskScore.model_id == model_id).order_by(RiskScore.risk_probability.desc()).limit(200).all()


@router.get("/model-cards")
def model_cards(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(ModelCard).join(MLModel, ModelCard.model_id == MLModel.id).order_by(ModelCard.created_at.desc())
    if user.role != "admin":
        query = query.filter(MLModel.created_by == user.id)
    return query.all()


@router.get("/model-cards/{model_card_id}")
def model_card(model_card_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    card = db.get(ModelCard, model_card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Model card not found")
    model = db.get(MLModel, card.model_id)
    if model and user.role != "admin" and model.created_by != user.id:
        raise HTTPException(status_code=403, detail="Model card access denied")
    return card
