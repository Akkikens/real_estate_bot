"""
Auth router — signup, login, refresh, password reset, user info.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from api.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: Optional[str] = None
    phone: Optional[str] = None
    market_id: str = "bay_area"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    market_id: str
    subscription_tier: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class PreferencesResponse(BaseModel):
    max_price: Optional[float] = None
    down_payment_pct: Optional[float] = None
    strategy: Optional[str] = None
    target_cities: Optional[list[str]] = None
    must_haves: Optional[list[str]] = None
    deal_breakers: Optional[list[str]] = None
    scoring_weight_overrides: Optional[dict] = None
    alert_channels: Optional[dict] = None
    alert_time: Optional[str] = None
    rental_alert_time: Optional[str] = None
    alert_score_threshold: Optional[float] = None
    timezone: Optional[str] = None

class PreferencesUpdate(BaseModel):
    max_price: Optional[float] = None
    down_payment_pct: Optional[float] = None
    strategy: Optional[str] = None
    target_cities: Optional[list[str]] = None
    must_haves: Optional[list[str]] = None
    deal_breakers: Optional[list[str]] = None
    scoring_weight_overrides: Optional[dict] = None
    alert_channels: Optional[dict] = None
    alert_time: Optional[str] = None
    rental_alert_time: Optional[str] = None
    alert_score_threshold: Optional[float] = None
    timezone: Optional[str] = None

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    market_id: Optional[str] = None


# ── DB dependency ─────────────────────────────────────────────────────────────

def _get_db():
    from database.db import get_session_factory, init_db
    init_db()
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json_loads(val: Optional[str]):
    """Safely parse JSON string to Python object."""
    if not val:
        return None
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None

def _prefs_to_response(prefs) -> PreferencesResponse:
    return PreferencesResponse(
        max_price=prefs.max_price,
        down_payment_pct=prefs.down_payment_pct,
        strategy=prefs.strategy,
        target_cities=_json_loads(prefs.target_cities),
        must_haves=_json_loads(prefs.must_haves),
        deal_breakers=_json_loads(prefs.deal_breakers),
        scoring_weight_overrides=_json_loads(prefs.scoring_weight_overrides),
        alert_channels=_json_loads(prefs.alert_channels),
        alert_time=prefs.alert_time,
        rental_alert_time=prefs.rental_alert_time,
        alert_score_threshold=prefs.alert_score_threshold,
        timezone=prefs.timezone,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(body: SignupRequest, db: Session = Depends(_get_db)):
    from database.models import User, UserPreferences

    # Check duplicate email
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        phone=body.phone,
        market_id=body.market_id,
    )
    db.add(user)
    db.flush()

    # Create default preferences
    prefs = UserPreferences(user_id=user.id)
    db.add(prefs)
    db.commit()

    logger.info("New user signup: %s", user.email)

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(_get_db)):
    from database.models import User

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(_get_db)):
    from database.models import User
    from jose import JWTError

    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse.model_validate(user)


# ── Profile endpoints ─────────────────────────────────────────────────────────

@router.get("/profile", response_model=dict)
def get_profile(user=Depends(get_current_user), db: Session = Depends(_get_db)):
    from database.models import UserPreferences

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    result = {
        "user": UserResponse.model_validate(user).model_dump(),
        "preferences": _prefs_to_response(prefs).model_dump() if prefs else None,
    }
    return result


@router.put("/profile")
def update_profile(
    body: ProfileUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.phone is not None:
        user.phone = body.phone
    if body.market_id is not None:
        from config.market import MARKETS
        if body.market_id not in MARKETS:
            raise HTTPException(status_code=400, detail=f"Unknown market: {body.market_id}")
        user.market_id = body.market_id
    db.commit()
    return {"status": "updated", "user": UserResponse.model_validate(user).model_dump()}


@router.put("/profile/preferences", response_model=PreferencesResponse)
def update_preferences(
    body: PreferencesUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    from database.models import UserPreferences

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    if not prefs:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)

    if body.max_price is not None:
        prefs.max_price = body.max_price
    if body.down_payment_pct is not None:
        prefs.down_payment_pct = body.down_payment_pct
    if body.strategy is not None:
        prefs.strategy = body.strategy
    if body.target_cities is not None:
        prefs.target_cities = json.dumps(body.target_cities)
    if body.must_haves is not None:
        prefs.must_haves = json.dumps(body.must_haves)
    if body.deal_breakers is not None:
        prefs.deal_breakers = json.dumps(body.deal_breakers)
    if body.scoring_weight_overrides is not None:
        prefs.scoring_weight_overrides = json.dumps(body.scoring_weight_overrides)
    if body.alert_channels is not None:
        prefs.alert_channels = json.dumps(body.alert_channels)
    if body.alert_time is not None:
        prefs.alert_time = body.alert_time
    if body.rental_alert_time is not None:
        prefs.rental_alert_time = body.rental_alert_time
    if body.alert_score_threshold is not None:
        prefs.alert_score_threshold = body.alert_score_threshold
    if body.timezone is not None:
        prefs.timezone = body.timezone

    db.commit()
    return _prefs_to_response(prefs)
