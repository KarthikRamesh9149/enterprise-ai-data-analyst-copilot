from __future__ import annotations

from pathlib import Path
from uuid import UUID

import mlflow
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Dataset, MLModel, ModelCard, RiskScore
from app.services.datasets import read_csv


def train_churn_model(db: Session, dataset: Dataset, user_id: UUID, target_column: str = "churned") -> MLModel:
    if settings.mlflow_tracking_uri.startswith("sqlite:///"):
        Path(settings.mlflow_tracking_uri.replace("sqlite:///", "", 1)).parent.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    df = read_csv(dataset.storage_path).dropna(subset=[target_column])
    ignored = {"customer_id", "signup_date", "churn_date", target_column}
    feature_cols = [c for c in df.columns if c not in ignored]
    X = df[feature_cols]
    y = pd.to_numeric(df[target_column], errors="coerce").fillna(0).astype(int)
    categorical = [c for c in feature_cols if X[c].dtype == "object"]
    numeric = [c for c in feature_cols if c not in categorical]
    preprocessor = ColumnTransformer(
        [("num", StandardScaler(), numeric), ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)]
    )
    pipeline = Pipeline([("prep", preprocessor), ("model", RandomForestClassifier(n_estimators=80, random_state=42, class_weight="balanced"))])
    if len(df) > 20 and y.nunique() > 1:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    else:
        X_train, X_test, y_train, y_test = X, X, y, y
    with mlflow.start_run(run_name="churn-random-forest") as run:
        pipeline.fit(X_train, y_train)
        proba = pipeline.predict_proba(X_test)[:, 1]
        pred = (proba >= 0.5).astype(int)
        metrics = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "f1": float(f1_score(y_test, pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, proba)) if y_test.nunique() > 1 else 0.5,
        }
        mlflow.log_params({"model_type": "RandomForestClassifier", "target": target_column, "features": len(feature_cols)})
        mlflow.log_metrics(metrics)
        importances = pipeline.named_steps["model"].feature_importances_
        feature_names = numeric + list(pipeline.named_steps["prep"].named_transformers_["cat"].get_feature_names_out(categorical))
        importance = sorted(
            [{"feature": feature_names[i], "importance": float(v)} for i, v in enumerate(importances)],
            key=lambda row: row["importance"],
            reverse=True,
        )[:20]
        model = MLModel(
            dataset_id=dataset.id,
            created_by=user_id,
            model_type="RandomForestClassifier",
            target_column=target_column,
            feature_columns=feature_cols,
            parameters={"n_estimators": 80, "class_weight": "balanced"},
            metrics=metrics,
            feature_importance=importance,
            mlflow_run_id=run.info.run_id,
            artifact_uri=run.info.artifact_uri,
        )
        db.add(model)
        db.flush()
        score_customers(db, model, dataset, pipeline)
        db.add(
            ModelCard(
                model_id=model.id,
                purpose="Identify currently active customers with elevated churn risk.",
                training_data_summary=f"Trained on {len(df)} synthetic/demo customer rows from {dataset.original_filename}.",
                feature_summary=", ".join(feature_cols),
                metrics_summary=str(metrics),
                intended_use="Portfolio demo and local decision support, not autonomous production decisions.",
                limitations="Synthetic data, no fairness review, retraining cadence not automated.",
                risk_notes="Use as an advisory signal with human review before customer actions.",
                monitoring_recommendations="Track drift, calibration, churn-rate stability, and false-positive outcomes.",
            )
        )
        return model


def score_customers(db: Session, model: MLModel, dataset: Dataset, pipeline: Pipeline) -> list[RiskScore]:
    df = read_csv(dataset.storage_path)
    X = df[model.feature_columns]
    proba = pipeline.predict_proba(X)[:, 1]
    rows: list[RiskScore] = []
    top_features = [item["feature"] for item in model.feature_importance[:3]]
    for idx, p in enumerate(proba):
        if str(df.iloc[idx].get("churned", "0")) in {"1", "True", "true"}:
            continue
        band = "high" if p >= 0.7 else "medium" if p >= 0.4 else "low"
        row = RiskScore(
            model_id=model.id,
            dataset_id=dataset.id,
            customer_id=str(df.iloc[idx].get("customer_id", idx)),
            risk_probability=float(p),
            risk_band=band,
            top_drivers=top_features,
            recommended_action="Prioritize retention outreach" if band == "high" else "Monitor engagement and support signals",
        )
        db.add(row)
        rows.append(row)
    return rows
