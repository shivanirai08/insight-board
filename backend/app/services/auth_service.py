"""Auth service — upsert users from Google (or dev) identity."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def upsert_google_user(
    db: Session,
    *,
    google_sub: str,
    email: str,
    full_name: str | None,
    picture_url: str | None,
) -> User:
    """
    Find by Google subject id; update profile fields; or create a new row.

    Google `sub` is the stable unique id (email can theoretically change).
    """
    user = db.scalar(select(User).where(User.google_sub == google_sub))
    if user is None:
        user = User(
            google_sub=google_sub,
            email=email,
            full_name=full_name,
            picture_url=picture_url,
        )
        db.add(user)
    else:
        user.email = email
        user.full_name = full_name
        user.picture_url = picture_url

    db.commit()
    db.refresh(user)
    return user
