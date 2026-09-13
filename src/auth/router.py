"""FastAPI Router for User Registration, Login, Token Refresh, and Profile Inspection."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.models import RefreshTokenRequest, TokenResponse, UserCreate, UserOut
from src.auth.service import (
    authenticate_user,
    create_user_tokens,
    get_current_user,
    refresh_tokens,
    register_user,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(user_in: UserCreate) -> UserOut:
    """Creates a new user account with hashed password."""
    return register_user(user_in)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to obtain Access and Refresh tokens",
)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """OAuth2 compatible token login.

    Accepts standard username/password form-data and returns RS256 JWT tokens.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_user_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renew an expired Access Token using a Refresh Token",
)
def refresh(payload: RefreshTokenRequest) -> TokenResponse:
    """Validates the refresh token and returns a new Access Token."""
    return refresh_tokens(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current authenticated user profile",
)
def read_current_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    """Returns the profile of the currently authenticated user."""
    return current_user
