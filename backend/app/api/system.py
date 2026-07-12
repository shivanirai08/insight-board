"""
System / infra routes — health checks that prove the stack is wired.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["system"])


class DbHealth(BaseModel):
    status: str
    database: str


@router.get("/db/health", response_model=DbHealth)
def db_health(db: Session = Depends(get_db)) -> DbHealth:
    """
    GET /api/db/health

    Runs SELECT 1 through SQLAlchemy. If Postgres is down, you get 503.
    This is your first real use of Depends(get_db).
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — surface connection errors as 503
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {exc.__class__.__name__}",
        ) from exc
    return DbHealth(status="ok", database="connected")
