"""
InsightBoard FastAPI application entrypoint.

Mental model:
  uvicorn loads THIS module, finds `app`, and starts an ASGI server.
  Every HTTP request becomes: path → router → path operation function → response.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from app.api.routes import api_router
from app.config import settings
from app.dash_app import create_dash_app
from app.db.base import Base
from app.db.session import engine

# Import models so Base.metadata knows about every table before create_all().
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_application: FastAPI):
    """
    Startup / shutdown hook.

    On startup we create tables if they do not exist (fine for learning).
    Later you can replace this with Alembic migrations for production.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown hooks (close pools, etc.) would go here.


def create_app() -> FastAPI:
    """
    Application factory — builds and configures the FastAPI instance.

    Why a function instead of a bare `app = FastAPI()` at module level?
    - Easier testing (create a fresh app per test)
    - Clear place to wire middleware, routers, and lifecycle hooks
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Analytics API for InsightBoard — CSV in, KPIs and charts out.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Session cookie required by Authlib to store OAuth "state" (CSRF protection).
    application.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # CORS: browsers block cross-origin API calls unless we allow the React origin.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount all versioned / feature routers under one place.
    application.include_router(api_router)

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """Liveness probe — used by you locally and by cloud load balancers later."""
        return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}

    @application.get("/analytics", include_in_schema=False)
    def analytics_redirect() -> RedirectResponse:
        """Dash expects a trailing slash when mounted under a subpath."""
        return RedirectResponse(url="/analytics/")

    # Dash (Flask/WSGI) lives beside the REST API — same process, denser analyst UI.
    dash_app = create_dash_app()
    application.mount("/analytics/", WSGIMiddleware(dash_app.server))

    return application


app = create_app()
