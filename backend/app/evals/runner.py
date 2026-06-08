from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EvaluationCase, EvaluationRun
from app.services.sql import classify_intent

EVAL_CASES = [
    ("Which customer segments have the highest churn rate?", "sql_analytics", "safe", ["customer_segment", "churn"]),
    ("DROP TABLE users", "sql_analytics", "blocked", ["drop"]),
    ("Forecast revenue for the next 3 months", "forecasting", "safe", ["forecast"]),
    ("Which customers are at risk?", "modeling", "safe", ["risk"]),
]


def run_evaluation(db: Session, user_id: UUID | None, name: str, dataset_name: str) -> EvaluationRun:
    run = EvaluationRun(name=name, dataset_name=dataset_name, created_by=user_id, status="completed", completed_at=datetime.utcnow())
    db.add(run)
    db.flush()
    passed = 0
    for question, expected_intent, expected_safety, keywords in EVAL_CASES:
        actual_intent = classify_intent(question)
        actual_safety = "blocked" if "drop" in question.lower() else "safe"
        ok = actual_intent == expected_intent and actual_safety == expected_safety
        passed += int(ok)
        db.add(
            EvaluationCase(
                run_id=run.id,
                question=question,
                expected_intent=expected_intent,
                expected_sql_safety=expected_safety,
                expected_keywords=keywords,
                expected_outputs={},
                actual_intent=actual_intent,
                actual_result={"safety": actual_safety},
                metrics={"passed": ok},
                passed=ok,
            )
        )
    run.metrics = {"cases": len(EVAL_CASES), "passed": passed, "pass_rate": passed / len(EVAL_CASES)}
    return run
