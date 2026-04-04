"""
JWT authentication utilities for the HouseMatch API.

Provides:
- Password hashing (bcrypt via passlib)
- JWT token creation & verification (access + refresh tokens)
- FastAPI dependency for extracting the current user from Authorization header
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# ── Config ────────────────────────────────────────────────────────────────────

# In production, set JWT_SECRET in .env. Fallback generates a random key per
# process restart (safe for dev, but tokens won't survive restarts).
JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_urlsafe(48))
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

# ── Password hashing ─────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT tokens ────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, extra: dict | None = None) -> str:
    """Create a short-lived access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises JWTError on failure."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ── FastAPI dependencies ──────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def _get_db():
    """Yield a SQLAlchemy session (mirrors api.main.get_db)."""
    from database.db import get_session_factory, init_db
    init_db()
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(_get_db),
):
    """
    Extract and validate the JWT from the Authorization header.
    Returns the User ORM object or raises 401.
    """
    from database.models import User

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(_get_db),
):
    """
    Like get_current_user but returns None instead of 401 for unauthenticated requests.
    Useful for endpoints that work with or without auth (e.g., property list).
    """
    from database.models import User

    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
