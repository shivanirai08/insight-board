"""Auth-related response schemas."""

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    """Safe user shape returned to clients — never include secrets."""

    id: int
    email: EmailStr
    full_name: str | None = None
    picture_url: str | None = None

    model_config = {"from_attributes": True}


class DevLoginRequest(BaseModel):
    email: EmailStr = Field(default="dev@example.com")
    full_name: str = Field(default="Dev User", max_length=255)
