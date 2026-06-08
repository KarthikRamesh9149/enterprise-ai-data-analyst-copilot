from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID

import duckdb
import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Dataset, DatasetColumn, DatasetProfile

REQUIRED_CHURN_COLUMNS = {
    "customer_id",
    "signup_date",
    "plan_type",
    "monthly_revenue",
    "total_revenue",
    "contract_type",
    "tenure_months",
    "support_tickets",
    "usage_minutes",
    "feature_usage_score",
    "payment_failures",
    "region",
    "customer_segment",
    "churned",
    "churn_date",
}

SENSITIVE_PATTERNS = ["email", "phone", "ssn", "credit_card", "password", "token", "secret"]


def safe_table_name(name: str, dataset_id: UUID) -> str:
    stem = re.sub(r"[^a-zA-Z0-9_]+", "_", Path(name).stem.lower()).strip("_")[:48]
    return f"ds_{stem}_{str(dataset_id).replace('-', '')[:8]}"


def read_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def upload_csv(db: Session, file: UploadFile, user_id: UUID) -> Dataset:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename).suffix.lower()
    stored_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.sha256(file.filename.encode()).hexdigest()[:10]}{suffix}"
    storage_path = upload_dir / stored_name
    total = 0
    hasher = hashlib.sha256()
    with storage_path.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            total += len(chunk)
            if total > settings.max_upload_bytes:
                storage_path.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
            hasher.update(chunk)
            out.write(chunk)
    content_hash = hasher.hexdigest()
    try:
        df = read_csv(storage_path)
    except Exception as exc:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="CSV parsing failed") from exc
    if len(df.columns) > 200:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="CSV has too many columns")
    dataset = Dataset(
        filename=stored_name,
        original_filename=Path(file.filename).name,
        uploaded_by=user_id,
        storage_path=str(storage_path),
        row_count=len(df),
        column_count=len(df.columns),
        file_size=total,
        content_hash=content_hash,
        status="uploaded",
    )
    db.add(dataset)
    db.flush()
    dataset.duckdb_table_name = safe_table_name(file.filename, dataset.id)
    profile_dataset(db, dataset)
    return dataset


def validate_dataset(db: Session, dataset: Dataset) -> dict:
    df = read_csv(dataset.storage_path)
    warnings: list[str] = []
    missing_required = sorted(REQUIRED_CHURN_COLUMNS - set(df.columns))
    if missing_required:
        warnings.append(f"Missing required churn columns: {', '.join(missing_required)}")
    if "signup_date" in df.columns and pd.to_datetime(df["signup_date"], errors="coerce").isna().any():
        warnings.append("Invalid signup_date values detected")
    if "monthly_revenue" in df.columns and (pd.to_numeric(df["monthly_revenue"], errors="coerce") < 0).any():
        warnings.append("Negative monthly_revenue values detected")
    if "total_revenue" in df.columns and (pd.to_numeric(df["total_revenue"], errors="coerce") < 0).any():
        warnings.append("Negative total_revenue values detected")
    if "customer_id" in df.columns and df["customer_id"].duplicated().any():
        warnings.append("Duplicate customer_id values detected")
    if "churned" in df.columns:
        churn_rate = float(pd.to_numeric(df["churned"], errors="coerce").fillna(0).mean())
        if churn_rate < 0.05 or churn_rate > 0.95:
            warnings.append("Potential class imbalance in churned target")
    sensitive = [c for c in df.columns if any(pattern in c.lower() for pattern in SENSITIVE_PATTERNS)]
    if sensitive:
        warnings.append(f"Sensitive columns detected: {', '.join(sensitive)}")
    quality = max(0.0, 100.0 - len(warnings) * 12.5 - (len(missing_required) * 8))
    dataset.validation_status = "passed" if not missing_required and not any("Negative" in w for w in warnings) else "warning"
    dataset.validation_summary = {
        "warnings": warnings,
        "missing_required_columns": missing_required,
        "sensitive_columns": sensitive,
        "row_count": len(df),
        "column_count": len(df.columns),
    }
    dataset.quality_score = quality
    return dataset.validation_summary


def profile_dataset(db: Session, dataset: Dataset) -> DatasetProfile:
    df = read_csv(dataset.storage_path)
    db.query(DatasetColumn).filter(DatasetColumn.dataset_id == dataset.id).delete()
    for col in df.columns:
        series = df[col]
        numeric = pd.to_numeric(series, errors="coerce")
        is_numeric = numeric.notna().sum() > max(1, len(series) * 0.6)
        db.add(
            DatasetColumn(
                dataset_id=dataset.id,
                column_name=col,
                inferred_type="numeric" if is_numeric else str(series.dtype),
                nullable=bool(series.isna().any()),
                missing_count=int(series.isna().sum()),
                missing_pct=float(series.isna().mean() * 100),
                unique_count=int(series.nunique(dropna=True)),
                min_value=str(numeric.min()) if is_numeric else str(series.dropna().astype(str).min() if not series.dropna().empty else ""),
                max_value=str(numeric.max()) if is_numeric else str(series.dropna().astype(str).max() if not series.dropna().empty else ""),
                mean_value=float(numeric.mean()) if is_numeric else None,
                std_value=float(numeric.std()) if is_numeric else None,
                sample_values=[str(x) for x in series.dropna().head(5).tolist()],
                warnings=["sensitive"] if any(pattern in col.lower() for pattern in SENSITIVE_PATTERNS) else [],
            )
        )
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    profile = DatasetProfile(
        dataset_id=dataset.id,
        profile_json={
            "columns": list(df.columns),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "numeric_summary": df.describe(include="all").fillna("").astype(str).to_dict(),
        },
        quality_score=max(0, 100 - missing_cells / max(1, df.size) * 100 - duplicate_rows),
        row_count=len(df),
        column_count=len(df.columns),
        missing_cells=missing_cells,
        duplicate_rows=duplicate_rows,
        warnings=[],
    )
    db.query(DatasetProfile).filter(DatasetProfile.dataset_id == dataset.id).delete()
    db.add(profile)
    dataset.row_count = len(df)
    dataset.column_count = len(df.columns)
    dataset.quality_score = profile.quality_score
    return profile


def load_to_duckdb(dataset: Dataset) -> None:
    Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(settings.duckdb_path)
    con.execute(f"CREATE OR REPLACE TABLE {dataset.duckdb_table_name} AS SELECT * FROM read_csv_auto(?)", [dataset.storage_path])
    con.close()
    dataset.status = "loaded"
    dataset.loaded_at = datetime.utcnow()


def sample_rows(dataset: Dataset, limit: int = 25) -> list[dict]:
    return read_csv(dataset.storage_path).head(limit).fillna("").to_dict(orient="records")
