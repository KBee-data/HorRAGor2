"""Pydantic schemas for User Authentication, Profiles, and JWT Tokens."""

from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, EmailStr, Field


# --- User Schemas ---
class UserBase(BaseModel):
    """Base user properties shared across request and response models."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User email address")


class UserCreate(UserBase):
    """Payload required to register a new user."""
    password: str = Field(..., min_length=6, description="Plain-text password (will be hashed)")


class UserLogin(BaseModel):
    """Payload required to log in."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Plain-text password")


class UserOut(UserBase):
    """Safe user profile representation returned by the API (no password hash)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserInDB(UserOut):
    """Internal user model stored in the database, including the hashed password."""
    hashed_password: str


# --- Token Schemas ---
class TokenResponse(BaseModel):
    """OAuth2 compatible token response containing Access and Refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds
    user: UserOut


class RefreshTokenRequest(BaseModel):
    """Payload sent by the client to renew an expired access token."""
    refresh_token: str
