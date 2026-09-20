"""Security and JWT token generation using RS256 asymmetric cryptography.

Provides:
1. Password hashing and verification via pwdlib (Argon2 / Bcrypt).
2. RS256 Access Token and Refresh Token creation using RSA Private Key.
3. Token decoding and validation using RSA Public Key.
4. OAuth2 password bearer dependency for route protection.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from src.auth.keys import get_rsa_keys

# Load the persistent RSA key pair
private_pem, public_pem = get_rsa_keys()

# FastAPI OAuth2 scheme pointing to our login endpoint (/auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Modern password hasher (Argon2 / Bcrypt)
password_hash = PasswordHash.recommended()


# --- Password Hashing Utilities ---
def hash_password(password: str) -> str:
    """Hashes a plain-text password."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    return password_hash.verify(plain_password, hashed_password)


# --- JWT Token Utilities (RS256) ---
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Creates a short-lived RS256 signed Access Token (default 30 min)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": str(uuid.uuid4()),
    })
    # Sign with RSA Private Key
    return jwt.encode(to_encode, private_pem, algorithm="RS256")


def create_refresh_token(
    username: str,
    family_id: str | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, str, str]:
    """Creates a long-lived RS256 signed Refresh Token (default 7 days) with token rotation IDs."""
    token_id = str(uuid.uuid4())
    fam_id = family_id or str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))

    payload = {
        "sub": username,
        "type": "refresh",
        "family_id": fam_id,
        "jti": token_id,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    # Sign with RSA Private Key
    refresh_token = jwt.encode(payload, private_pem, algorithm="RS256")
    return refresh_token, token_id, fam_id


def decode_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT token using the RSA Public Key."""
    return jwt.decode(token, public_pem, algorithms=["RS256"])
