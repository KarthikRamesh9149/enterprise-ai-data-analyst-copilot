from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "viewer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class QuestionRequest(BaseModel):
    dataset_id: UUID
    question: str = Field(min_length=3, max_length=2000)


class ValidateSQLRequest(BaseModel):
    dataset_id: UUID
    sql: str = Field(min_length=6, max_length=10000)


class ApproveSQLRequest(BaseModel):
    query_id: UUID
    reviewer_notes: str | None = None


class ExecuteSQLRequest(BaseModel):
    query_id: UUID


class AgentRunRequest(BaseModel):
    dataset_id: UUID | None = None
    question: str


class ChurnTrainRequest(BaseModel):
    dataset_id: UUID
    target_column: str = "churned"


class ChurnScoreRequest(BaseModel):
    model_id: UUID


class ForecastRequest(BaseModel):
    dataset_id: UUID
    forecast_target: str = "total_revenue"
    horizon_months: int = Field(default=3, ge=1, le=24)


class ReportRequest(BaseModel):
    dataset_id: UUID | None = None
    agent_run_id: UUID | None = None
    title: str = "Executive Churn and Revenue Report"
    report_type: str = "executive"


class ApprovalReviewRequest(BaseModel):
    reviewer_notes: str | None = None


class EvalRunRequest(BaseModel):
    name: str = "mock-safety-and-intent-eval"
    dataset_name: str = "demo-churn"
