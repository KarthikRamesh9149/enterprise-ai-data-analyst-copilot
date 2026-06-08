from __future__ import annotations

from pathlib import Path
from uuid import UUID

import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Dataset, ForecastRun
from app.services.datasets import read_csv


def run_revenue_forecast(db: Session, dataset: Dataset, user_id: UUID, target: str, horizon: int) -> ForecastRun:
    if settings.mlflow_tracking_uri.startswith("sqlite:///"):
        Path(settings.mlflow_tracking_uri.replace("sqlite:///", "", 1)).parent.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    df = read_csv(dataset.storage_path)
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"])
        df = df.sort_values("month")
        y = pd.to_numeric(df[target], errors="coerce").fillna(method="ffill").fillna(0).to_numpy()
        x = np.arange(len(y)).reshape(-1, 1)
        labels = [str((df["month"].max() + pd.DateOffset(months=i + 1)).date()) for i in range(horizon)]
    else:
        monthly = df.groupby("signup_date", dropna=False)["total_revenue"].sum().reset_index()
        y = pd.to_numeric(monthly["total_revenue"], errors="coerce").fillna(0).to_numpy()
        x = np.arange(len(y)).reshape(-1, 1)
        labels = [f"period_{i + 1}" for i in range(horizon)]
        target = "total_revenue"
    model = LinearRegression().fit(x, y)
    future_x = np.arange(len(y), len(y) + horizon).reshape(-1, 1)
    forecast = model.predict(future_x)
    mae = float(np.mean(np.abs(model.predict(x) - y))) if len(y) else 0
    values = [{"period": labels[i], "forecast": float(max(0, forecast[i]))} for i in range(horizon)]
    with mlflow.start_run(run_name="revenue-forecast") as run:
        mlflow.log_params({"model_type": "LinearRegression", "horizon_months": horizon, "target": target})
        mlflow.log_metric("mae", mae)
        chart = {
            "type": "line",
            "data": [{"type": "scatter", "mode": "lines+markers", "x": labels, "y": [v["forecast"] for v in values]}],
            "layout": {"title": f"{target} forecast", "xaxis": {"title": "period"}, "yaxis": {"title": target}},
        }
        forecast_run = ForecastRun(
            dataset_id=dataset.id,
            created_by=user_id,
            forecast_target=target,
            horizon_months=horizon,
            model_type="LinearRegression",
            metrics={"mae": mae},
            forecast_values=values,
            chart_spec=chart,
            mlflow_run_id=run.info.run_id,
        )
        db.add(forecast_run)
        return forecast_run
