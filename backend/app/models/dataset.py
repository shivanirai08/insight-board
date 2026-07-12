"""
Dataset model — one uploaded (or sample) CSV after pandas cleaning.

`rows` stores cleaned records as JSON so arbitrary CSV schemas work without
a new SQL table per upload. On PostgreSQL this becomes JSONB.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str] = mapped_column(
        String(50),
        default="upload",
        doc="upload | sample",
    )
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    columns: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        default=list,
    )
    rows: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        default=list,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    owner: Mapped[User] = relationship("User", back_populates="datasets")
