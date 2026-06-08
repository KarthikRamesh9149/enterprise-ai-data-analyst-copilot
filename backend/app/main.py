from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, agent, analytics, approvals, auth, datasets, evals, forecasting, modeling, reports
from app.core.config import settings

app = FastAPI(title="Enterprise AI Data Analyst & Forecasting Copilot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env}


app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(analytics.router)
app.include_router(agent.router)
app.include_router(modeling.router)
app.include_router(forecasting.router)
app.include_router(reports.router)
app.include_router(approvals.router)
app.include_router(evals.router)
app.include_router(admin.router)
