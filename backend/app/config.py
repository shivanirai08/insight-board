"""
Central configuration loaded from environment variables / .env file.

Pydantic Settings reads env vars, coerces types, and fails fast if something
required is missing or the wrong type — better than scattered os.getenv calls.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "InsightBoard"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "postgresql+psycopg://insight:insight@localhost:5432/insightboard"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:5173"

    # Local shortcut for building UIs before Google OAuth credentials exist.
    # MUST stay false in production.
    ENABLE_DEV_LOGIN: bool = True


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — import `settings` or inject via Depends(get_settings)."""
    return Settings()


settings = get_settings()
