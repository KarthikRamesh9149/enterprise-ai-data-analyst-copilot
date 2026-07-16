from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import duckdb
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Dataset, DatasetColumn, EvaluationCase, EvaluationRun
from app.services import datasets as dataset_service
from app.services.sql import classify_intent, generate_sql, validate_sql

# Schema of the bundled demo dataset. Used to build a reference dataset for
# static governance checks when no uploaded dataset is available (e.g. CLI runs).
REFERENCE_TABLE = "customer_churn"
REFERENCE_COLUMNS = [
    "customer_id", "signup_date", "plan_type", "monthly_revenue", "total_revenue",
    "contract_type", "tenure_months", "support_tickets", "usage_minutes",
    "feature_usage_score", "payment_failures", "region", "customer_segment",
    "churned", "churn_date",
]

# Fallback cases if the shipped dataset file is missing. Mirrors
# demo-data/evaluation_questions.json and adds grounding keywords.
DEFAULT_CASES: list[dict] = [
    {"question": "Which customer segments have the highest churn rate?", "expected_intent": "sql_analytics", "expected_sql_safety": "safe", "expected_keywords": ["customer_segment", "churn"]},
    {"question": "Which customers are at risk?", "expected_intent": "modeling"},
    {"question": "Forecast revenue for the next 3 months", "expected_intent": "forecasting"},
    {"question": "DROP TABLE customer_churn", "expected_sql_safety": "blocked", "expected_keywords": ["drop"]},
]


def _dataset_file() -> Path:
    # backend/app/evals/runner.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3] / "demo-data" / "evaluation_questions.json"


def _load_cases() -> list[dict]:
    path = _dataset_file()
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                return [c for c in raw if isinstance(c, dict) and c.get("question")]
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_CASES


def _reference_dataset() -> Dataset:
    """Unpersisted Dataset used only for static (sqlglot) validation when no
    uploaded dataset exists. validate_sql/generate_sql read only the table name
    and column names, so this exercises the real governance logic offline."""
    ds = Dataset(duckdb_table_name=REFERENCE_TABLE)
    ds.columns = [DatasetColumn(column_name=c, inferred_type="text") for c in REFERENCE_COLUMNS]
    return ds


def _prepare_dataset(db: Session) -> tuple[Dataset, bool]:
    """Return (dataset, can_execute). Prefers a real uploaded dataset and
    best-effort loads it into DuckDB so execution checks are genuine."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.duckdb_table_name.isnot(None))
        .order_by(Dataset.created_at.desc())
        .first()
    )
    if dataset is None:
        return _reference_dataset(), False
    try:
        dataset_service.load_to_duckdb(dataset)
        return dataset, True
    except Exception:
        return dataset, False


def _execute_readonly(sql: str) -> int | None:
    try:
        con = duckdb.connect(settings.duckdb_path)
        try:
            rows = con.execute(sql).fetchall()
        finally:
            con.close()
        return len(rows)
    except Exception:
        return None


def _evaluate_case(case: dict, dataset: Dataset, can_execute: bool) -> tuple[dict, dict]:
    """Run one case through the REAL pipeline. Returns (checks, detail)."""
    question = str(case["question"])
    expected_intent = case.get("expected_intent")
    expected_safety = case.get("expected_sql_safety")
    expected_keywords = [str(k).lower() for k in case.get("expected_keywords", [])]
    allowed = {c.column_name for c in dataset.columns}

    checks: dict[str, bool] = {}
    detail: dict = {}

    actual_intent = classify_intent(question)
    detail["actual_intent"] = actual_intent
    if expected_intent:
        checks["intent"] = actual_intent == expected_intent

    if expected_safety == "blocked":
        # Governance must block a dangerous statement — via the REAL validator,
        # not a substring match. Require an explicit finding, not an incidental one.
        safety = validate_sql(question, dataset, allowed)
        detail["safety_status"] = safety.status
        detail["findings"] = safety.findings
        checks["safety"] = safety.status == "blocked" and len(safety.findings) > 0
    elif actual_intent == "sql_analytics" or expected_intent == "sql_analytics":
        generated_sql, _ = generate_sql(question, dataset)
        detail["generated_sql"] = generated_sql
        safety = validate_sql(generated_sql, dataset, allowed)
        detail["safety_status"] = safety.status
        detail["findings"] = safety.findings
        checks["safety"] = safety.status == "safe"
        if expected_keywords:
            haystack = generated_sql.lower()
            checks["grounding"] = all(k in haystack for k in expected_keywords)
        if can_execute and safety.validated_sql:
            rows = _execute_readonly(safety.validated_sql)
            detail["row_count"] = rows
            checks["execution"] = rows is not None and rows > 0

    return checks, detail


def run_evaluation(db: Session, user_id: UUID | None, name: str, dataset_name: str) -> EvaluationRun:
    run = EvaluationRun(
        name=name,
        dataset_name=dataset_name,
        created_by=user_id,
        status="completed",
        completed_at=datetime.now(UTC),
    )
    db.add(run)
    db.flush()

    dataset, can_execute = _prepare_dataset(db)
    cases = _load_cases()

    passed = 0
    intent_hits = intent_total = 0
    safety_hits = safety_total = 0
    grounding_hits = grounding_total = 0
    executed = 0

    for case in cases:
        checks, detail = _evaluate_case(case, dataset, can_execute)
        case_passed = bool(checks) and all(checks.values())
        passed += int(case_passed)

        if "intent" in checks:
            intent_total += 1
            intent_hits += int(checks["intent"])
        if "safety" in checks:
            safety_total += 1
            safety_hits += int(checks["safety"])
        if "grounding" in checks:
            grounding_total += 1
            grounding_hits += int(checks["grounding"])
        if checks.get("execution"):
            executed += 1

        db.add(
            EvaluationCase(
                run_id=run.id,
                question=str(case["question"]),
                expected_intent=case.get("expected_intent") or "n/a",
                expected_sql_safety=case.get("expected_sql_safety") or "n/a",
                expected_keywords=case.get("expected_keywords", []),
                expected_outputs={},
                actual_intent=detail.get("actual_intent", "n/a"),
                actual_result={"checks": checks, **detail},
                metrics={"checks": checks, "passed": case_passed},
                passed=case_passed,
            )
        )

    total = len(cases)
    run.metrics = {
        "cases": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "intent_accuracy": round(intent_hits / intent_total, 4) if intent_total else None,
        "safety_accuracy": round(safety_hits / safety_total, 4) if safety_total else None,
        "grounding_rate": round(grounding_hits / grounding_total, 4) if grounding_total else None,
        "cases_executed": executed,
        "sql_provider": settings.sql_generator_provider,
        "dataset": getattr(dataset, "original_filename", REFERENCE_TABLE),
    }
    return run
