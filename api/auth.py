"""
JWT authentication utilities for the HouseMatch API.

Supports two token flavours:
1. **Clerk session tokens** (RS256, verified via Clerk JWKS) — primary auth path
2. **Legacy HS256 tokens** (local JWT_SECRET) — kept for backwards compat / scripts

Flow for Clerk tokens:
- Decode the JWT header to check algorithm
- If RS256 → fetch Clerk's JWKS, verify signature, extract `sub` (Clerk user ID)
- Find-or-create a local User row keyed by `clerk_id`
"""

from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt, jwk
from jose.utils import base64url_decode
from passlib.context import CryptContext
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

# Legacy local JWT (for scripts / backwards compat)
JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_urlsafe(48))
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

# Clerk JWKS — derived from the publishable key's frontend API domain
# e.g. pk_test_Y29udGVudC13cmVuLTkzLmNsZXJrLmFjY291bnRzLmRldiQ → content-wren-93.clerk.accounts.dev
CLERK_JWKS_URL: str | None = os.getenv("CLERK_JWKS_URL")  # override if needed
CLERK_PUBLISHABLE_KEY: str | None = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")

_jwks_cache: dict | None = None


def _get_clerk_jwks_url() -> str | None:
    """Derive the Clerk JWKS URL from the publishable key or env override."""
    if CLERK_JWKS_URL:
        return CLERK_JWKS_URL
    if not CLERK_PUBLISHABLE_KEY:
        return None
    # pk_test_<base64 of domain>$ or pk_live_<base64 of domain>$
    try:
        import base64
        # Key format: pk_{env}_{base64_of_domain}
        encoded = CLERK_PUBLISHABLE_KEY.split("_", 2)[2]
        # Add padding
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += "=" * padding
        domain = base64.b64decode(encoded).decode("utf-8").rstrip("$")
        return f"https://{domain}/.well-known/jwks.json"
    except Exception as e:
        logger.warning("Could not derive Clerk JWKS URL from publishable key: %s", e)
        return None


async def _fetch_clerk_jwks() -> dict | None:
    """Fetch and cache Clerk's JWKS keys."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    url = _get_clerk_jwks_url()
    if not url:
        logger.warning("No Clerk JWKS URL configured — Clerk auth disabled")
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            logger.info("Fetched Clerk JWKS from %s (%d keys)", url, len(_jwks_cache.get("keys", [])))
            return _jwks_cache
    except Exception as e:
        logger.error("Failed to fetch Clerk JWKS from %s: %s", url, e)
        return None


def _fetch_clerk_jwks_sync() -> dict | None:
    """Synchronous version for use in sync FastAPI dependencies."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    url = _get_clerk_jwks_url()
    if not url:
        return None

    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        logger.info("Fetched Clerk JWKS from %s (%d keys)", url, len(_jwks_cache.get("keys", [])))
        return _jwks_cache
    except Exception as e:
        logger.error("Failed to fetch Clerk JWKS from %s: %s", url, e)
        return None


def _verify_clerk_token(token: str) -> dict | None:
    """
    Verify a Clerk RS256 JWT using JWKS.
    Returns the decoded payload or None if verification fails.
    """
    try:
        # Peek at the header to check algorithm
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            return None

        kid = header.get("kid")
        if not kid:
            return None

        jwks = _fetch_clerk_jwks_sync()
        if not jwks:
            return None

        # Find the matching key
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            # Key not found — maybe JWKS rotated; clear cache and retry once
            global _jwks_cache
            _jwks_cache = None
            jwks = _fetch_clerk_jwks_sync()
            if jwks:
                for key in jwks.get("keys", []):
                    if key.get("kid") == kid:
                        rsa_key = key
                        break

        if not rsa_key:
            logger.warning("Clerk JWKS key not found for kid=%s", kid)
            return None

        # Verify and decode
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,  # Clerk tokens don't always have aud
                "verify_iss": False,  # We trust the JWKS source
            },
        )
        return payload

    except JWTError as e:
        logger.debug("Clerk JWT verification failed: %s", e)
        return None
    except Exception as e:
        logger.warning("Unexpected error verifying Clerk token: %s", e)
        return None


# ── Password hashing ─────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Legacy JWT tokens ────────────────────────────────────────────────────────

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
    """Decode and validate a legacy JWT. Raises JWTError on failure."""
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


def _find_or_create_clerk_user(clerk_payload: dict, db: Session):
    """
    Given a verified Clerk JWT payload, find or create a local User.
    Clerk payload has: sub (clerk user ID), email, name, etc.
    """
    from database.models import User

    clerk_id = clerk_payload.get("sub")
    if not clerk_id:
        return None

    # Try to find by clerk_id first
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    if user:
        return user

    # Try to find by email (link existing account)
    email = clerk_payload.get("email")
    # Clerk might put email in different places
    if not email:
        # Some Clerk token formats use email_addresses
        email = clerk_payload.get("primary_email_address")
    if not email:
        # Use a placeholder — Clerk user ID as email
        email = f"{clerk_id}@clerk.user"

    user = db.query(User).filter(User.email == email).first()
    if user:
        # Link existing user to Clerk
        user.clerk_id = clerk_id
        db.commit()
        return user

    # Create new user
    name = clerk_payload.get("name")
    if not name:
        first = clerk_payload.get("first_name", "")
        last = clerk_payload.get("last_name", "")
        name = f"{first} {last}".strip() or None

    user = User(
        clerk_id=clerk_id,
        email=email,
        password_hash=None,
        name=name,
        market_id="bay_area",
        subscription_tier="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created new user from Clerk: id=%d clerk_id=%s email=%s", user.id, clerk_id, email)
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(_get_db),
):
    """
    Extract and validate the JWT from the Authorization header.
    Supports both Clerk (RS256) and legacy (HS256) tokens.
    Returns the User ORM object or raises 401.
    """
    from database.models import User

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try Clerk (RS256) first
    clerk_payload = _verify_clerk_token(token)
    if clerk_payload:
        user = _find_or_create_clerk_user(clerk_payload, db)
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to provision user from Clerk token",
        )

    # Fall back to legacy HS256 token
    try:
        payload = decode_token(token)
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

    user = db.query(User).filter(User.id == user_id).first()
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
    """
    from database.models import User

    if credentials is None:
        return None

    token = credentials.credentials

    # Try Clerk first
    clerk_payload = _verify_clerk_token(token)
    if clerk_payload:
        return _find_or_create_clerk_user(clerk_payload, db)

    # Legacy fallback
    try:
        payload = decode_token(token)
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()
