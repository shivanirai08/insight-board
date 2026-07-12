"""
Auth routes — Google OAuth handshake, JWT issuance, /me, optional dev login.

Flow (Google):
  1. Browser → GET /api/auth/google/login
  2. Redirect to Google consent screen
  3. Google → GET /api/auth/google/callback?code=...
  4. We exchange code for profile, upsert User, mint JWT
  5. Redirect to FRONTEND_URL/auth/callback?token=<jwt>
"""

from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import DevLoginRequest, TokenResponse, UserPublic
from app.services.auth_service import upsert_google_user

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID or "unset",
    client_secret=settings.GOOGLE_CLIENT_SECRET or "unset",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def _google_configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


@router.get("/google/login")
async def google_login(request: Request):
    """Start Google OAuth — redirects the browser to Google."""
    if not _google_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET in backend/.env — or use POST /api/auth/dev-login "
                "while ENABLE_DEV_LOGIN=true."
            ),
        )
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google redirects here after consent.

    We never show the JWT in an HTML page — we bounce to the React app with ?token=.
    """
    if not _google_configured():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth failed: {exc.error}",
        ) from exc

    userinfo = token.get("userinfo")
    if not userinfo:
        # Some flows need an explicit userinfo call
        userinfo = await oauth.google.userinfo(token=token)

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    if not google_sub or not email:
        raise HTTPException(status_code=400, detail="Google profile missing sub/email")

    user = upsert_google_user(
        db,
        google_sub=google_sub,
        email=email,
        full_name=userinfo.get("name"),
        picture_url=userinfo.get("picture"),
    )
    access_token = create_access_token(subject=str(user.id), extra={"email": user.email})

    query = urlencode({"token": access_token})
    return RedirectResponse(url=f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback?{query}")


@router.get("/me", response_model=UserPublic)
def read_me(user: User = Depends(get_current_user)) -> User:
    """Return the logged-in user — requires Authorization: Bearer <jwt>."""
    return user


@router.post("/dev-login", response_model=TokenResponse)
def dev_login(body: DevLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Local-only shortcut so you can build React/Dash before Google Console is ready.

    Disabled unless ENABLE_DEV_LOGIN=true. Never enable in production.
    """
    if not settings.ENABLE_DEV_LOGIN:
        raise HTTPException(status_code=404, detail="Not found")

    user = upsert_google_user(
        db,
        google_sub=f"dev:{body.email}",
        email=str(body.email),
        full_name=body.full_name,
        picture_url=None,
    )
    access_token = create_access_token(subject=str(user.id), extra={"email": user.email})
    return TokenResponse(access_token=access_token)
