"""
Root API router.

Each feature (auth, data, upload) gets its own router module.
We include them here so `main.py` only needs one `include_router` call.
"""

from fastapi import APIRouter

from app.api import auth, hello, system
from app.config import settings

api_router = APIRouter(prefix=settings.API_PREFIX)
api_router.include_router(hello.router, tags=["hello"])
api_router.include_router(system.router)
api_router.include_router(auth.router)
