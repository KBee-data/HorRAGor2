"""Authentication service: User management, login verification, token rotation, and route protection."""

import json
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, status
import jwt

from src.auth.models import TokenResponse, UserCreate, UserInDB, UserOut
from src.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    oauth2_scheme,
    verify_password,
)

# Persistent storage file for user accounts (persists across restarts)
USERS_FILE = Path("data/users.json")


def _load_users() -> dict[str, dict[str, Any]]:
    """Loads the user database from disk."""
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_users(users: dict[str, dict[str, Any]]) -> None:
    """Persists user dictionary to data/users.json."""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2, default=str), encoding="utf-8")


def get_user_by_username(username: str) -> UserInDB | None:
    """Finds a user by exact username (case-insensitive)."""
    users = _load_users()
    for u in users.values():
        if u["username"].lower() == username.lower():
            return UserInDB(**u)
    return None


def get_user_by_email(email: str) -> UserInDB | None:
    """Finds a user by email address."""
    users = _load_users()
    for u in users.values():
        if u["email"].lower() == email.lower():
            return UserInDB(**u)
    return None


def register_user(user_in: UserCreate) -> UserOut:
    """Registers a new user, hashing their password before saving."""
    if get_user_by_username(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' is already taken.",
        )
    if get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_in.email}' is already registered.",
        )

    # Hash the password with Argon2/Bcrypt
    hashed_pwd = hash_password(user_in.password)

    user_db = UserInDB(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pwd,
    )

    users = _load_users()
    users[user_db.id] = user_db.model_dump()
    _save_users(users)

    return UserOut(**user_db.model_dump())


def authenticate_user(username_or_email: str, plain_password: str) -> UserInDB | None:
    """Verifies user credentials against stored password hash."""
    user = get_user_by_username(username_or_email) or get_user_by_email(username_or_email)
    if not user:
        return None
    if not verify_password(plain_password, user.hashed_password):
        return None
    return user


def create_user_tokens(user: UserInDB) -> TokenResponse:
    """Generates a fresh Access Token and Refresh Token pair for a user."""
    access_token = create_access_token(data={"sub": user.username, "email": user.email})
    refresh_token, _, _ = create_refresh_token(username=user.username)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut(**user.model_dump()),
    )


def refresh_tokens(refresh_token: str) -> TokenResponse:
    """Validates a Refresh Token and generates a brand new Access Token."""
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a refresh token.",
        )

    username = payload.get("sub")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return create_user_tokens(user)


# --- FastAPI Dependency for Route Protection ---
def get_current_user(token: str = Depends(oauth2_scheme)) -> UserOut:
    """Extracts and validates the JWT Bearer token from the incoming HTTP request."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user_by_username(username)
    if user is None or not user.is_active:
        raise credentials_exception

    return UserOut(**user.model_dump())
