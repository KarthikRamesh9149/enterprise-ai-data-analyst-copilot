from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Dataset, MLModel, Report


def generate_report(db: Session, user_id: UUID, title: str, dataset: Dataset | None = None, agent_run_id: UUID | None = None) -> Report:
    latest_model = db.query(MLModel).order_by(MLModel.created_at.desc()).first()
    markdown = f"""# {title}

## Facts
- Dataset: {dataset.original_filename if dataset else "not selected"}.
- Rows: {dataset.row_count if dataset else "n/a"}.
- Quality score: {round(dataset.quality_score, 2) if dataset else "n/a"}.

## Predictions
- Latest churn model metrics: {latest_model.metrics if latest_model else "No model trained yet"}.

## Recommendations
- Prioritize high-risk customers with payment failures, low usage, and high support burden.
- Review month-to-month contracts and targeted annual-plan incentives.
- Monitor forecast variance monthly before changing budget allocation.

## Limitations
- Demo/local providers are deterministic and do not use external LLM calls.
- Synthetic data is suitable for portfolio demonstration, not production decisioning.
"""
    html = "<article>" + markdown.replace("\n", "<br />") + "</article>"
    Path(settings.upload_dir).parent.mkdir(parents=True, exist_ok=True)
    reports_dir = Path("storage/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report = Report(
        created_by=user_id,
        dataset_id=dataset.id if dataset else None,
        agent_run_id=agent_run_id,
        title=title,
        report_type="executive",
        markdown_content=markdown,
        html_content=html,
        file_path="",
    )
    db.add(report)
    db.flush()
    path = reports_dir / f"{report.id}.md"
    path.write_text(markdown, encoding="utf-8")
    report.file_path = str(path)
    return report
