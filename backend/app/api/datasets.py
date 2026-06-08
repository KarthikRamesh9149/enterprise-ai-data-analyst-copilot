from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_permission
from app.db.models import Dataset, DatasetColumn, DatasetProfile, User
from app.db.session import get_db
from app.services.audit import audit
from app.services.datasets import load_to_duckdb, sample_rows, upload_csv, validate_dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])


def can_read_dataset(dataset: Dataset, user: User) -> bool:
    return user.role in {"admin", "reviewer"} or dataset.uploaded_by == user.id


def can_process_dataset(dataset: Dataset, user: User) -> bool:
    return user.role == "admin" or (user.role == "analyst" and dataset.uploaded_by == user.id)


def get_dataset_or_404(db: Session, dataset_id: UUID, user: User | None = None, write: bool = False) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if user:
        allowed = can_process_dataset(dataset, user) if write else can_read_dataset(dataset, user)
        if not allowed:
            raise HTTPException(status_code=403, detail="Dataset access denied")
    return dataset


@router.post("/upload")
def upload_dataset(
    file: UploadFile = File(...),
    user: User = Depends(require_permission("datasets:upload")),
    db: Session = Depends(get_db),
):
    dataset = upload_csv(db, file, user.id)
    audit(db, user.id, "dataset.upload", "dataset", str(dataset.id), {"filename": dataset.original_filename})
    db.commit()
    return dataset


@router.get("")
def list_datasets(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(Dataset).order_by(Dataset.created_at.desc())
    if user.role not in {"admin", "reviewer"}:
        query = query.filter(Dataset.uploaded_by == user.id)
    return query.all()


@router.get("/{dataset_id}")
def get_dataset(dataset_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return get_dataset_or_404(db, dataset_id, user)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id, user, write=True)
    if user.role != "admin" and dataset.uploaded_by != user.id:
        raise HTTPException(status_code=403, detail="Cannot delete this dataset")
    db.delete(dataset)
    audit(db, user.id, "dataset.delete", "dataset", str(dataset_id))
    db.commit()
    return {"message": "Dataset deleted"}


@router.get("/{dataset_id}/schema")
def schema(dataset_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_dataset_or_404(db, dataset_id, user)
    return db.query(DatasetColumn).filter(DatasetColumn.dataset_id == dataset_id).all()


@router.get("/{dataset_id}/profile")
def profile(dataset_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    get_dataset_or_404(db, dataset_id, user)
    return db.query(DatasetProfile).filter(DatasetProfile.dataset_id == dataset_id).order_by(DatasetProfile.created_at.desc()).first()


@router.get("/{dataset_id}/sample")
def sample(dataset_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id, user)
    return sample_rows(dataset)


@router.post("/{dataset_id}/validate")
def validate(dataset_id: UUID, user: User = Depends(require_permission("datasets:validate")), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id, user, write=True)
    summary = validate_dataset(db, dataset)
    audit(db, user.id, "dataset.validate", "dataset", str(dataset_id), summary)
    db.commit()
    return summary


@router.post("/{dataset_id}/load-to-duckdb")
def load(dataset_id: UUID, user: User = Depends(require_permission("datasets:validate")), db: Session = Depends(get_db)):
    dataset = get_dataset_or_404(db, dataset_id, user, write=True)
    load_to_duckdb(dataset)
    audit(db, user.id, "dataset.load_duckdb", "dataset", str(dataset_id), {"table": dataset.duckdb_table_name})
    db.commit()
    return dataset
