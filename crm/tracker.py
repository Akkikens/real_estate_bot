"""
CRM Tracker
============
Records outreach activity, tracks responses, and manages follow-up reminders.
All outreach goes through here; nothing is sent without explicit control.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from config import settings
from database.models import OutreachRecord, Property
from outreach.templates import draft_outreach

logger = logging.getLogger(__name__)


def create_draft(
    db: Session,
    prop: Property,
    outreach_type: str = "initial",
) -> OutreachRecord:
    """
    Create a draft outreach record for a property.
    Does NOT send anything — that requires explicit approval.
    """
    draft = draft_outreach(prop, outreach_type=outreach_type)

    record = OutreachRecord(
        property_id=prop.id,
        agent_name=prop.agent_name,
        agent_email=prop.agent_email,
        agent_phone=prop.agent_phone,
        outreach_type=outreach_type,
        subject=draft["subject"],
        draft_body=draft["body"],
        status="draft",
        next_follow_up=datetime.utcnow() + timedelta(days=6),
    )
    db.add(record)
    db.flush()
    logger.info("Created draft outreach for %s (%s)", prop.address, outreach_type)
    return record


def mark_sent(db: Session, record: OutreachRecord) -> None:
    """Mark an outreach record as sent."""
    record.status = "sent"
    record.sent_at = datetime.utcnow()
    record.next_follow_up = datetime.utcnow() + timedelta(days=6)
    logger.info("Marked outreach #%d as sent", record.id)


def record_reply(
    db: Session,
    record: OutreachRecord,
    reply_body: str,
    sentiment: str = "neutral",
) -> None:
    """Record an agent reply against an outreach record."""
    record.status = "replied"
    record.reply_received_at = datetime.utcnow()
    record.reply_body = reply_body
    record.reply_sentiment = sentiment
    record.next_follow_up = None  # Clear auto-follow-up once replied
    logger.info("Reply recorded for outreach #%d — sentiment: %s", record.id, sentiment)


def get_follow_ups_due(db: Session) -> list[OutreachRecord]:
    """Return all outreach records that need a follow-up today."""
    now = datetime.utcnow()
    return (
        db.query(OutreachRecord)
        .filter(
            OutreachRecord.status == "sent",
            OutreachRecord.next_follow_up <= now,
            OutreachRecord.reply_received_at.is_(None),
        )
        .all()
    )


def get_crm_summary(db: Session) -> dict:
    """Return a summary of CRM activity."""
    total = db.query(OutreachRecord).count()
    drafts = db.query(OutreachRecord).filter(OutreachRecord.status == "draft").count()
    sent = db.query(OutreachRecord).filter(OutreachRecord.status == "sent").count()
    replied = db.query(OutreachRecord).filter(OutreachRecord.status == "replied").count()
    due = len(get_follow_ups_due(db))

    return {
        "total": total,
        "drafts": drafts,
        "sent": sent,
        "replied": replied,
        "follow_ups_due": due,
        "reply_rate": f"{replied / sent * 100:.1f}%" if sent > 0 else "n/a",
    }
