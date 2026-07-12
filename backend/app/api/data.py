"""
Analytics endpoints — frontend-agnostic JSON for React and Dash.

  GET /api/data/{dataset_id}/summary
  GET /api/data/{dataset_id}/trends
  GET /api/data/{dataset_id}/breakdown
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import BreakdownResponse, SummaryResponse, TrendsResponse
from app.services import analytics as analytics_service

router = APIRouter(prefix="/data", tags=["analytics"])


def _owned_dataset(db: Session, user: User, dataset_id: int) -> Dataset:
    dataset = db.scalar(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == user.id)
    )
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/summary", response_model=SummaryResponse)
def get_summary(
    dataset_id: int,
    date_from: str | None = Query(default=None, description="YYYY-MM-DD"),
    date_to: str | None = Query(default=None, description="YYYY-MM-DD"),
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    dataset = _owned_dataset(db, user, dataset_id)
    payload = analytics_service.build_summary(
        list(dataset.columns or []),
        list(dataset.rows or []),
        date_from=date_from,
        date_to=date_to,
        category=category,
    )
    return SummaryResponse(dataset_id=dataset.id, **payload)


@router.get("/{dataset_id}/trends", response_model=TrendsResponse)
def get_trends(
    dataset_id: int,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrendsResponse:
    dataset = _owned_dataset(db, user, dataset_id)
    payload = analytics_service.build_trends(
        list(dataset.columns or []),
        list(dataset.rows or []),
        date_from=date_from,
        date_to=date_to,
        category=category,
    )
    return TrendsResponse(dataset_id=dataset.id, **payload)


@router.get("/{dataset_id}/breakdown", response_model=BreakdownResponse)
def get_breakdown(
    dataset_id: int,
    group_by: str | None = Query(default=None, description="Column name, e.g. region"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreakdownResponse:
    dataset = _owned_dataset(db, user, dataset_id)
    payload = analytics_service.build_breakdown(
        list(dataset.columns or []),
        list(dataset.rows or []),
        group_by=group_by,
        date_from=date_from,
        date_to=date_to,
        category=category,
    )
    return BreakdownResponse(dataset_id=dataset.id, **payload)
