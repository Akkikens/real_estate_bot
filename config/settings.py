"""
Central settings loader — reads from .env and provides typed defaults.
All secrets and tunable values live here; nothing is hardcoded elsewhere.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
load_dotenv(Path(__file__).parents[1] / ".env")


def _bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


def _float(key: str, default: float = 0.0) -> float:
    return float(os.getenv(key, default))


def _int(key: str, default: int = 0) -> int:
    return int(os.getenv(key, default))


def _list(key: str, default: str = "") -> list[str]:
    raw = os.getenv(key, default)
    return [v.strip() for v in raw.split(",") if v.strip()]


# ─── Database ────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./real_estate.db")

# ─── Buyer profile ───────────────────────────────────────────────────────────
BUYER_MAX_PRICE: float = _float("BUYER_MAX_PRICE", 750_000)
BUYER_DOWN_PAYMENT: float = _float("BUYER_DOWN_PAYMENT", 55_000)
BUYER_TARGET_CITIES: list[str] = _list(
    "BUYER_TARGET_CITIES",
    "Richmond,San Pablo,El Cerrito,Albany,Berkeley,Oakland,Hayward,Fremont,San Leandro",
)

# ─── Scoring ─────────────────────────────────────────────────────────────────
ALERT_SCORE_THRESHOLD: float = _float("ALERT_SCORE_THRESHOLD", 65)

# ─── Email ───────────────────────────────────────────────────────────────────
ALERT_EMAIL_ENABLED: bool = _bool("ALERT_EMAIL_ENABLED")
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = _int("SMTP_PORT", 587)
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASS: str = os.getenv("SMTP_PASS", "")
ALERT_TO_EMAIL: str = os.getenv("ALERT_TO_EMAIL", "")

# ─── SMS ─────────────────────────────────────────────────────────────────────
SMS_ENABLED: bool = _bool("SMS_ENABLED")
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
ALERT_TO_PHONE: str = os.getenv("ALERT_TO_PHONE", "")

# ─── WhatsApp (via Twilio) ────────────────────────────────────────────────────
WHATSAPP_ENABLED: bool = _bool("WHATSAPP_ENABLED")
WHATSAPP_FROM_NUMBER: str = os.getenv("WHATSAPP_FROM_NUMBER", "")  # whatsapp:+1...
WHATSAPP_TO_NUMBER: str = os.getenv("WHATSAPP_TO_NUMBER", "")      # whatsapp:+1...

# Auto-prefix whatsapp: if user forgot (Twilio requires it)
if WHATSAPP_FROM_NUMBER and not WHATSAPP_FROM_NUMBER.startswith("whatsapp:"):
    WHATSAPP_FROM_NUMBER = f"whatsapp:{WHATSAPP_FROM_NUMBER}"
if WHATSAPP_TO_NUMBER and not WHATSAPP_TO_NUMBER.startswith("whatsapp:"):
    WHATSAPP_TO_NUMBER = f"whatsapp:{WHATSAPP_TO_NUMBER}"

# ─── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_ENABLED: bool = _bool("TELEGRAM_ENABLED")
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ─── Mortgage / underwriting ─────────────────────────────────────────────────
MORTGAGE_RATE: float = _float("MORTGAGE_RATE", 0.0725)
MORTGAGE_TERM_YEARS: int = _int("MORTGAGE_TERM_YEARS", 30)
PROPERTY_TAX_RATE: float = _float("PROPERTY_TAX_RATE", 0.0125)
INSURANCE_RATE: float = _float("INSURANCE_RATE", 0.005)
PMI_RATE: float = _float("PMI_RATE", 0.005)
MAINTENANCE_RATE: float = _float("MAINTENANCE_RATE", 0.01)
VACANCY_RATE: float = _float("VACANCY_RATE", 0.05)

ROOM_RENTAL_LOW: float = _float("ROOM_RENTAL_LOW", 1_000)
ROOM_RENTAL_MID: float = _float("ROOM_RENTAL_MID", 1_400)
ROOM_RENTAL_HIGH: float = _float("ROOM_RENTAL_HIGH", 1_800)

# ─── Rate limiting ────────────────────────────────────────────────────────────
REDFIN_DELAY_SECONDS: float = _float("REDFIN_DELAY_SECONDS", 3.0)
ZILLOW_DELAY_SECONDS: float = _float("ZILLOW_DELAY_SECONDS", 5.0)
REALTOR_DELAY_SECONDS: float = _float("REALTOR_DELAY_SECONDS", 4.0)
CRAIGSLIST_DELAY_SECONDS: float = _float("CRAIGSLIST_DELAY_SECONDS", 5.0)
REQUEST_TIMEOUT_SECONDS: float = _float("REQUEST_TIMEOUT_SECONDS", 20.0)

# ─── Outreach ─────────────────────────────────────────────────────────────────
OUTREACH_MODE: str = os.getenv("OUTREACH_MODE", "draft")  # draft | approve | auto

# ─── Scoring weights validation ──────────────────────────────────────────────
# Validate that YAML weights sum to ~1.0 at import time to catch config errors.
import logging as _logging
from pathlib import Path as _Path
try:
    import yaml as _yaml
    _weights_path = _Path(__file__).parent / "scoring_weights.yaml"
    if _weights_path.exists():
        with open(_weights_path) as _f:
            _w = _yaml.safe_load(_f).get("weights", {})
        _total = sum(v for v in _w.values() if isinstance(v, (int, float)))
        if abs(_total - 1.0) > 0.02:
            _logging.getLogger(__name__).warning(
                "Scoring weights in scoring_weights.yaml sum to %.3f "
                "(expected 1.0). Scores may drift — please check config.",
                _total,
            )
except Exception as _exc:
    _logging.getLogger(__name__).warning(
        "Could not validate scoring weights: %s", _exc
    )
