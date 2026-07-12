"""Dataset API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetMeta(BaseModel):
    id: int
    name: str
    original_filename: str | None = None
    source: str
    row_count: int
    columns: list[str]
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetDetail(DatasetMeta):
    """Includes a small preview of rows (not the full dump by default)."""

    preview_rows: list[dict[str, Any]] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    dataset_id: int
    row_count: int
    total_revenue: float
    total_units: float
    avg_revenue: float
    growth_pct: float | None
    metrics_available: dict[str, str | None]
    filter_options: dict[str, list[str]]


class TrendPoint(BaseModel):
    date: str
    value: float


class TrendsResponse(BaseModel):
    dataset_id: int
    date_column: str | None
    value_column: str | None
    points: list[TrendPoint]


class BreakdownItem(BaseModel):
    label: str
    value: float


class BreakdownResponse(BaseModel):
    dataset_id: int
    group_by: str | None
    value_column: str | None
    items: list[BreakdownItem]
