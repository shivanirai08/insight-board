"""
Dataset upload / sample load / list / detail.

All routes require a logged-in user (JWT). Datasets are scoped to owner_id.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import DatasetDetail, DatasetMeta
from app.services.csv_processing import clean_csv_bytes

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _get_owned_dataset(db: Session, user: User, dataset_id: int) -> Dataset:
    dataset = db.scalar(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == user.id)
    )
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("", response_model=list[DatasetMeta])
def list_datasets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Dataset]:
    return list(
        db.scalars(
            select(Dataset).where(Dataset.owner_id == user.id).order_by(Dataset.created_at.desc())
        )
    )


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetDetail:
    dataset = _get_owned_dataset(db, user, dataset_id)
    preview = list(dataset.rows[:20]) if dataset.rows else []
    return DatasetDetail(
        id=dataset.id,
        name=dataset.name,
        original_filename=dataset.original_filename,
        source=dataset.source,
        row_count=dataset.row_count,
        columns=list(dataset.columns or []),
        notes=dataset.notes,
        created_at=dataset.created_at,
        preview_rows=preview,
    )


@router.post("/upload", response_model=DatasetMeta, status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dataset:
    """
    Multipart upload: field name `file` (+ optional `name`).

    pandas cleans the CSV; we store columns + rows as JSON on the Dataset.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    columns, rows, row_count = clean_csv_bytes(raw)

    dataset = Dataset(
        owner_id=user.id,
        name=name or Path(file.filename).stem,
        original_filename=file.filename,
        source="upload",
        row_count=row_count,
        columns=columns,
        rows=rows,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.post("/sample", response_model=DatasetMeta, status_code=status.HTTP_201_CREATED)
def load_sample_dataset(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dataset:
    """Load the bundled sales sample CSV as a new dataset for this user."""
    sample_path = Path(settings.SAMPLE_DATA_PATH)
    if not sample_path.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"Sample file missing at {sample_path}. Check SAMPLE_DATA_PATH.",
        )

    raw = sample_path.read_bytes()
    columns, rows, row_count = clean_csv_bytes(raw)

    dataset = Dataset(
        owner_id=user.id,
        name="Sample Sales",
        original_filename=sample_path.name,
        source="sample",
        row_count=row_count,
        columns=columns,
        rows=rows,
        notes="Bundled demo dataset for InsightBoard",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    dataset = _get_owned_dataset(db, user, dataset_id)
    db.delete(dataset)
    db.commit()
