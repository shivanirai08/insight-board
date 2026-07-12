"""
Database engine and session factory.

Pattern you will use everywhere:
  db: Session = Depends(get_db)

FastAPI calls get_db(), yields a session, then closes it after the response.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# echo=True prints SQL — useful while learning; turn off in production via DEBUG.
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # drop dead connections before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — one Session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Return True if SELECT 1 succeeds against the configured database."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
