"""
Alert Notifier
==============
Sends alerts through configured channels (email, SMS, Telegram, console).

Alert types:
  • new_match     — new property exceeds score threshold
  • price_drop    — watched property has significant price drop
  • status_change — active → pending or sold
  • follow_up_due — CRM reminder

Rate limiting: At most 1 alert per property per alert_type per day.
"""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy.orm import Session

from config import settings
from database.models import Alert, Property

logger = logging.getLogger(__name__)


# ── Email ─────────────────────────────────────────────────────────────────────


def _send_email(subject: str, body: str) -> bool:
    if not settings.ALERT_EMAIL_ENABLED:
        logger.debug("Email alerts disabled.")
        return False
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        logger.warning("Email alert configured but SMTP credentials missing.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.ALERT_TO_EMAIL

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, settings.ALERT_TO_EMAIL, msg.as_string())

        logger.info("Email alert sent: %s", subject)
        return True
    except Exception as exc:
        logger.error("Email alert failed: %s", exc)
        return False


# ── SMS (Twilio) ──────────────────────────────────────────────────────────────


def _send_sms(body: str) -> bool:
    if not settings.SMS_ENABLED:
        return False
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body[:1600],
            from_=settings.TWILIO_FROM_NUMBER,
            to=settings.ALERT_TO_PHONE,
        )
        logger.info("SMS alert sent.")
        return True
    except ImportError:
        logger.warning("twilio not installed. Run: pip install twilio")
        return False
    except Exception as exc:
        logger.error("SMS alert failed: %s", exc)
        return False


# ── WhatsApp (Twilio) ─────────────────────────────────────────────────────


def _send_whatsapp(body: str) -> bool:
    if not settings.WHATSAPP_ENABLED:
        return False
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body[:1600],
            from_=settings.WHATSAPP_FROM_NUMBER,
            to=settings.WHATSAPP_TO_NUMBER,
        )
        logger.info("WhatsApp alert sent.")
        return True
    except ImportError:
        logger.warning("twilio not installed. Run: pip install twilio")
        return False
    except Exception as exc:
        logger.error("WhatsApp alert failed: %s", exc)
        return False


# ── Telegram ──────────────────────────────────────────────────────────────────


def _send_telegram(body: str) -> bool:
    if not settings.TELEGRAM_ENABLED:
        return False
    try:
        import httpx
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = httpx.post(url, json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": body})
        resp.raise_for_status()
        logger.info("Telegram alert sent.")
        return True
    except Exception as exc:
        logger.error("Telegram alert failed: %s", exc)
        return False


# ── Core alert builder ────────────────────────────────────────────────────────


def _build_alert_message(prop: Property, alert_type: str, extra: str = "") -> tuple[str, str]:
    """Build subject + body for an alert."""
    price = f"${prop.list_price:,.0f}" if prop.list_price else "?"
    score = f"{prop.total_score:.0f}/100" if prop.total_score else "?"
    url = prop.listing_url or "No URL"

    if alert_type == "new_match":
        subject = f"🏠 New Match: {prop.address} — Score {score}"
        body = (
            f"New property match!\n\n"
            f"Address: {prop.address}, {prop.city}\n"
            f"Price:   {price}\n"
            f"Score:   {score} ({prop.rating or '?'})\n"
            f"Beds/Ba: {prop.beds}BR / {prop.baths}BA\n"
            f"Sqft:    {prop.sqft or '?'}\n"
            f"DOM:     {prop.days_on_market or '?'} days\n"
            f"\n{prop.score_explanation or ''}\n"
            f"\nURL: {url}"
        )
    elif alert_type == "price_drop":
        subject = f"💰 Price Drop: {prop.address} → {price}"
        body = (
            f"Price reduction detected!\n\n"
            f"Address: {prop.address}, {prop.city}\n"
            f"New Price: {price}\n"
            f"Score: {score}\n"
            f"{extra}\n"
            f"\nURL: {url}"
        )
    elif alert_type == "status_change":
        subject = f"⚡ Status Change: {prop.address} → {prop.status.upper()}"
        body = (
            f"Listing status changed!\n\n"
            f"Address: {prop.address}, {prop.city}\n"
            f"New Status: {prop.status.upper()}\n"
            f"Price: {price}\n"
            f"\nURL: {url}"
        )
    elif alert_type == "follow_up_due":
        subject = f"🔔 Follow-up Due: {prop.address}"
        body = (
            f"Time to follow up with the agent!\n\n"
            f"Address: {prop.address}, {prop.city}\n"
            f"Price: {price}\n"
            f"{extra}\n"
            f"\nURL: {url}"
        )
    else:
        subject = f"Alert: {prop.address}"
        body = f"{prop.address}, {prop.city} — {extra}"

    return subject, body


def _already_alerted_today(db: Session, prop_id: str, alert_type: str) -> bool:
    """Prevent duplicate alerts for same property+type within 24h."""
    cutoff = datetime.utcnow() - timedelta(hours=22)
    existing = (
        db.query(Alert)
        .filter(
            Alert.property_id == prop_id,
            Alert.alert_type == alert_type,
            Alert.sent == True,
            Alert.sent_at >= cutoff,
        )
        .first()
    )
    return existing is not None


def send_alert(
    db: Session,
    prop: Property,
    alert_type: str,
    extra: str = "",
    force: bool = False,
) -> Alert:
    """
    Send an alert for a property.
    Rate-limited: won't resend same type within 24h unless force=True.
    Returns the Alert record.
    """
    if not force and _already_alerted_today(db, prop.id, alert_type):
        logger.debug("Alert suppressed (already sent today): %s / %s", prop.address, alert_type)
        alert = Alert(
            property_id=prop.id,
            alert_type=alert_type,
            message=f"Suppressed duplicate alert.",
            sent=False,
        )
        db.add(alert)
        return alert

    subject, body = _build_alert_message(prop, alert_type, extra)

    # Always log to console
    logger.info("ALERT [%s] %s | %s", alert_type.upper(), prop.address, subject)

    channels_used = []
    errors = []

    # Email
    if settings.ALERT_EMAIL_ENABLED:
        ok = _send_email(subject, body)
        if ok:
            channels_used.append("email")
        else:
            errors.append("email_failed")

    # SMS
    if settings.SMS_ENABLED:
        ok = _send_sms(f"{subject}\n\n{body[:500]}")
        if ok:
            channels_used.append("sms")

    # WhatsApp
    if settings.WHATSAPP_ENABLED:
        ok = _send_whatsapp(f"*{subject}*\n\n{body}")
        if ok:
            channels_used.append("whatsapp")

    # Telegram
    if settings.TELEGRAM_ENABLED:
        ok = _send_telegram(f"*{subject}*\n\n{body}")
        if ok:
            channels_used.append("telegram")

    alert = Alert(
        property_id=prop.id,
        alert_type=alert_type,
        message=body,
        channels=",".join(channels_used) or "console_only",
        sent=True,
        sent_at=datetime.utcnow(),
        error=", ".join(errors) if errors else None,
    )
    db.add(alert)
    prop.alert_sent = True
    return alert


def check_and_alert(db: Session, props: list[Property]) -> int:
    """
    Evaluate a list of properties and send alerts for any that qualify.
    Returns count of alerts sent.
    """
    count = 0
    threshold = settings.ALERT_SCORE_THRESHOLD

    for prop in props:
        if prop.is_archived:
            continue

        score = prop.total_score or 0

        # New match alert
        if score >= threshold and not prop.alert_sent:
            send_alert(db, prop, "new_match")
            count += 1

        # Status change
        if prop.status in ("pending", "sold") and prop.is_watched:
            send_alert(db, prop, "status_change")
            count += 1

    return count
