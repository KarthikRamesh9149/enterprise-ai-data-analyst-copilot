from __future__ import annotations

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.evals.runner import run_evaluation


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run = run_evaluation(db, None, "cli-mock-eval", "demo-churn")
        db.commit()
        print(run.metrics)
    finally:
        db.close()


if __name__ == "__main__":
    main()
