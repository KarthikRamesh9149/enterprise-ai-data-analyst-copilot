from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator

from app.db.base import Base


class GUID(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class JsonType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


def ts() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = ts()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[uuid.UUID] = uuid_pk()
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    duckdb_table_name: Mapped[str | None] = mapped_column(String(128), unique=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    validation_status: Mapped[str] = mapped_column(String(32), default="pending")
    validation_summary: Mapped[dict] = mapped_column(JsonType(), default=dict)
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = ts()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    loaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    columns: Mapped[list[DatasetColumn]] = relationship(cascade="all, delete-orphan")


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"
    id: Mapped[uuid.UUID] = uuid_pk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    column_name: Mapped[str] = mapped_column(String(128), index=True)
    inferred_type: Mapped[str] = mapped_column(String(64))
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    missing_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_pct: Mapped[float] = mapped_column(Float, default=0)
    unique_count: Mapped[int] = mapped_column(Integer, default=0)
    min_value: Mapped[str | None] = mapped_column(String(255))
    max_value: Mapped[str | None] = mapped_column(String(255))
    mean_value: Mapped[float | None] = mapped_column(Float)
    std_value: Mapped[float | None] = mapped_column(Float)
    sample_values: Mapped[list] = mapped_column(JsonType(), default=list)
    warnings: Mapped[list] = mapped_column(JsonType(), default=list)
    created_at: Mapped[datetime] = ts()


class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"
    id: Mapped[uuid.UUID] = uuid_pk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    profile_json: Mapped[dict] = mapped_column(JsonType(), default=dict)
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_cells: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list] = mapped_column(JsonType(), default=list)
    created_at: Mapped[datetime] = ts()


class AnalyticsQuestion(Base):
    __tablename__ = "analytics_questions"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="generated")
    created_at: Mapped[datetime] = ts()


class GeneratedSQLQuery(Base):
    __tablename__ = "generated_sql_queries"
    id: Mapped[uuid.UUID] = uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("analytics_questions.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    generated_sql: Mapped[str] = mapped_column(Text)
    validated_sql: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    safety_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    safety_findings: Mapped[list] = mapped_column(JsonType(), default=list)
    approval_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    execution_status: Mapped[str] = mapped_column(String(32), default="not_started", index=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = ts()
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SQLExecutionResult(Base):
    __tablename__ = "sql_execution_results"
    id: Mapped[uuid.UUID] = uuid_pk()
    sql_query_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("generated_sql_queries.id"), index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    columns: Mapped[list] = mapped_column(JsonType(), default=list)
    result_preview: Mapped[list] = mapped_column(JsonType(), default=list)
    result_storage_path: Mapped[str | None] = mapped_column(String(500))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = ts()


class Chart(Base):
    __tablename__ = "charts"
    id: Mapped[uuid.UUID] = uuid_pk()
    sql_query_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("generated_sql_queries.id"), index=True)
    chart_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    chart_spec: Mapped[dict] = mapped_column(JsonType(), default=dict)
    created_at: Mapped[datetime] = ts()


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    final_report_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = ts()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentTrace(Base):
    __tablename__ = "agent_traces"
    id: Mapped[uuid.UUID] = uuid_pk()
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), index=True)
    node_name: Mapped[str] = mapped_column(String(128), index=True)
    input_summary: Mapped[str] = mapped_column(Text)
    output_summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = ts()


class EDAResult(Base):
    __tablename__ = "eda_results"
    id: Mapped[uuid.UUID] = uuid_pk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("agent_runs.id"))
    summary: Mapped[dict] = mapped_column(JsonType(), default=dict)
    charts: Mapped[list] = mapped_column(JsonType(), default=list)
    created_at: Mapped[datetime] = ts()


class MLModel(Base):
    __tablename__ = "ml_models"
    id: Mapped[uuid.UUID] = uuid_pk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    model_type: Mapped[str] = mapped_column(String(64))
    target_column: Mapped[str] = mapped_column(String(128))
    feature_columns: Mapped[list] = mapped_column(JsonType(), default=list)
    parameters: Mapped[dict] = mapped_column(JsonType(), default=dict)
    metrics: Mapped[dict] = mapped_column(JsonType(), default=dict)
    feature_importance: Mapped[list] = mapped_column(JsonType(), default=list)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(128))
    artifact_uri: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), default="trained")
    approval_status: Mapped[str] = mapped_column(String(32), default="approved")
    created_at: Mapped[datetime] = ts()


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id: Mapped[uuid.UUID] = uuid_pk()
    model_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ml_models.id"), index=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(128), index=True)
    risk_probability: Mapped[float] = mapped_column(Float)
    risk_band: Mapped[str] = mapped_column(String(32), index=True)
    top_drivers: Mapped[list] = mapped_column(JsonType(), default=list)
    recommended_action: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = ts()


class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    id: Mapped[uuid.UUID] = uuid_pk()
    dataset_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("datasets.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    forecast_target: Mapped[str] = mapped_column(String(128))
    horizon_months: Mapped[int] = mapped_column(Integer)
    model_type: Mapped[str] = mapped_column(String(64))
    metrics: Mapped[dict] = mapped_column(JsonType(), default=dict)
    forecast_values: Mapped[list] = mapped_column(JsonType(), default=list)
    chart_spec: Mapped[dict] = mapped_column(JsonType(), default=dict)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = ts()


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[uuid.UUID] = uuid_pk()
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("datasets.id"))
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("agent_runs.id"))
    title: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[str] = mapped_column(String(64))
    markdown_content: Mapped[str] = mapped_column(Text)
    html_content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ready")
    file_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = ts()


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[uuid.UUID] = uuid_pk()
    requested_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    action_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    request_reason: Mapped[str] = mapped_column(Text)
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = ts()
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ModelCard(Base):
    __tablename__ = "model_cards"
    id: Mapped[uuid.UUID] = uuid_pk()
    model_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ml_models.id"), index=True)
    purpose: Mapped[str] = mapped_column(Text)
    training_data_summary: Mapped[str] = mapped_column(Text)
    feature_summary: Mapped[str] = mapped_column(Text)
    metrics_summary: Mapped[str] = mapped_column(Text)
    intended_use: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str] = mapped_column(Text)
    risk_notes: Mapped[str] = mapped_column(Text)
    monitoring_recommendations: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = ts()


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255))
    dataset_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="completed")
    metrics: Mapped[dict] = mapped_column(JsonType(), default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    created_at: Mapped[datetime] = ts()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"
    id: Mapped[uuid.UUID] = uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("evaluation_runs.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    expected_intent: Mapped[str] = mapped_column(String(64))
    expected_sql_safety: Mapped[str] = mapped_column(String(32))
    expected_keywords: Mapped[list] = mapped_column(JsonType(), default=list)
    expected_outputs: Mapped[dict] = mapped_column(JsonType(), default=dict)
    actual_intent: Mapped[str] = mapped_column(String(64))
    actual_result: Mapped[dict] = mapped_column(JsonType(), default=dict)
    metrics: Mapped[dict] = mapped_column(JsonType(), default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = ts()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), index=True)
    event_metadata: Mapped[dict] = mapped_column(JsonType(), default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = ts()


class SystemMetric(Base):
    __tablename__ = "system_metrics"
    id: Mapped[uuid.UUID] = uuid_pk()
    metric_name: Mapped[str] = mapped_column(String(128), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    dimensions: Mapped[dict] = mapped_column(JsonType(), default=dict)
    created_at: Mapped[datetime] = ts()


Index("ix_queries_user_dataset", GeneratedSQLQuery.user_id, GeneratedSQLQuery.dataset_id)
Index("ix_audit_resource", AuditLog.resource_type, AuditLog.resource_id)
