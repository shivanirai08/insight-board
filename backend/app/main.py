"""
InsightBoard FastAPI application entrypoint.

Mental model:
  uvicorn loads THIS module, finds `app`, and starts an ASGI server.
  Every HTTP request becomes: path → router → path operation function → response.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.config import settings


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
    )

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

    return application


app = create_app()
