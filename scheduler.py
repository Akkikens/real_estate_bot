"""
Scheduler
=========
Runs the bot on a schedule using APScheduler.
Can be deployed as a standalone process or via Docker.

Default schedule:
  • Every 4 hours: ingest new listings + score + alert
  • Every morning at 8am: generate full daily report
  • Every 30 minutes: check for follow-ups due in CRM

Usage:
    python scheduler.py         # start the scheduler (runs indefinitely)
    python scheduler.py --once  # run the full pipeline once then exit
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scheduler.log", mode="a", encoding="utf-8"),
    ],
)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def _run_pipeline(listing_type: str):
    """
    Core pipeline: ingest → score → alert.
    listing_type: "sale" or "rental"
    """
    from config import settings
    from database.db import get_db, init_db
    from database.models import Property
    from ingestion.normalizer import upsert_property
    from ingestion.sanity import check as sanity_check, log_anomaly
    from scoring.engine import score_and_update
    from scoring.rental_scorer import score_rental_and_update
    from alerts.notifier import check_and_alert

    init_db()

    from ingestion.redfin_adapter import RedfinAdapter
    from ingestion.zillow_adapter import ZillowAdapter
    from ingestion.realtor_adapter import RealtorAdapter
    from ingestion.craigslist_adapter import CraigslistAdapter
    from ingestion.enrichment import enrich_properties

    if listing_type == "rental":
        max_price = float(os.getenv("RENTAL_MAX_PRICE", "2500"))
        cities = [c.strip() for c in os.getenv(
            "RENTAL_TARGET_CITIES",
            "Oakland,Berkeley,Alameda,Emeryville,Albany,El Cerrito,Richmond"
        ).split(",") if c.strip()]
        adapters = [
            RedfinAdapter(listing_type="rental"),
            CraigslistAdapter(listing_type="rental"),
        ]
        scorer = score_rental_and_update
    else:
        max_price = settings.BUYER_MAX_PRICE
        cities = settings.BUYER_TARGET_CITIES
        adapters = [
            RedfinAdapter(),
            ZillowAdapter(),
            RealtorAdapter(),
            CraigslistAdapter(),
        ]
        scorer = score_and_update

    label = listing_type.upper()
    total_new = 0
    with get_db() as db:
        for adapter in adapters:
            logger.info("[%s] Ingesting from %s...", label, adapter.source_name)
            try:
                listings = adapter.fetch_listings(cities, max_price)
                for normalized in listings:
                    normalized["listing_type"] = listing_type
                    sanity = sanity_check(normalized)
                    if not sanity.passed:
                        log_anomaly(db, normalized, sanity)
                        continue
                    prop, created = upsert_property(db, normalized)
                    scorer(prop)
                    if created:
                        total_new += 1
            except Exception as exc:
                logger.error("Adapter %s failed: %s", adapter.source_name, exc)

        props = db.query(Property).filter(
            Property.status == "active",
            Property.is_archived == False,
            Property.listing_type == listing_type,
        ).all()

        # Enrich properties missing BART distance (geocode + haversine)
        n_enriched = enrich_properties(db, props)
        if n_enriched:
            logger.info("[%s] Enriched %d properties with BART distance", label, n_enriched)
            # Re-score enriched properties
            for prop in props:
                scorer(prop)

        n_alerts = check_and_alert(db, props)
        db.commit()

    logger.info("[%s] Pipeline complete. New: %d | Alerts sent: %d", label, total_new, n_alerts)


def run_ingest_pipeline():
    """Scheduled job: ingest FOR-SALE listings → score → alert."""
    _run_pipeline("sale")


def run_rental_pipeline():
    """Scheduled job: ingest RENTAL listings → score → send SMS digest."""
    _run_pipeline("rental")
    _send_rental_digest()


def _send_rental_digest():
    """Send digest via SMS + WhatsApp with top rental leads."""
    from database.db import get_db, init_db
    from database.models import Property
    from config import settings

    if not settings.SMS_ENABLED and not settings.WHATSAPP_ENABLED:
        return

    init_db()
    with get_db() as db:
        # Get new rentals from last 24 hours, ordered by score then price
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        rentals = (
            db.query(Property)
            .filter(
                Property.listing_type == "rental",
                Property.status == "active",
                Property.is_archived == False,
                Property.first_seen_at >= cutoff,
            )
            .order_by(Property.total_score.desc().nullsfirst(), Property.list_price.asc())
            .limit(10)
            .all()
        )

        if not rentals:
            logger.info("No new rentals in last 24h — skipping digest SMS.")
            return

        lines = [f"🏠 Top {len(rentals)} New Rentals Today:\n"]
        for i, p in enumerate(rentals, 1):
            beds = f"{p.beds}BR" if p.beds else "?"
            price = f"${p.list_price:,.0f}" if p.list_price else "?"
            city = p.city or "?"
            lines.append(f"{i}. {city} {beds} {price}")
            lines.append(f"   {p.address or '?'}")
            if p.listing_url:
                lines.append(f"   {p.listing_url}")
            lines.append("")

        body = "\n".join(lines)

        try:
            from twilio.rest import Client
        except ImportError:
            logger.warning("twilio not installed — cannot send rental digest. Run: pip install twilio")
            return

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            for chunk_start in range(0, len(body), 1500):
                chunk = body[chunk_start:chunk_start + 1500]
                # SMS
                if settings.SMS_ENABLED:
                    client.messages.create(
                        body=chunk,
                        from_=settings.TWILIO_FROM_NUMBER,
                        to=settings.ALERT_TO_PHONE,
                    )
                # WhatsApp
                if settings.WHATSAPP_ENABLED:
                    client.messages.create(
                        body=chunk,
                        from_=settings.WHATSAPP_FROM_NUMBER,
                        to=settings.WHATSAPP_TO_NUMBER,
                    )
            channels = []
            if settings.SMS_ENABLED:
                channels.append("SMS")
            if settings.WHATSAPP_ENABLED:
                channels.append("WhatsApp")
            logger.info("Rental digest sent via %s (%d listings).", "+".join(channels), len(rentals))
        except Exception as exc:
            logger.error("Rental digest failed: %s", exc)


def run_daily_report():
    """Morning report job."""
    from database.db import get_db, init_db
    from reports.generator import full_report

    init_db()
    with get_db() as db:
        data = full_report(db)

        top = data["top_opportunities"]
        logger.info("=== DAILY REPORT ===")
        logger.info("Top opportunities:")
        for prop in top[:5]:
            logger.info(
                "  %s, %s — $%s — score %.0f",
                prop.address, prop.city,
                f"{prop.list_price:,.0f}" if prop.list_price else "?",
                prop.total_score or 0,
            )


def run_crm_check():
    """Check for follow-ups due."""
    from database.db import get_db, init_db
    from crm.tracker import get_follow_ups_due

    init_db()
    with get_db() as db:
        due = get_follow_ups_due(db)
        if due:
            logger.info("CRM: %d follow-ups due!", len(due))
            for r in due:
                prop = r.property
                logger.info("  → %s (%s)", prop.address if prop else "?", r.agent_name or "?")


def start_scheduler():
    """Start APScheduler with all jobs."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BlockingScheduler(timezone="America/Los_Angeles")

    # Every 4 hours: for-sale listings ingest + alert pipeline
    scheduler.add_job(
        run_ingest_pipeline,
        trigger=IntervalTrigger(hours=4),
        id="sale_pipeline",
        name="For-Sale Ingest + Score + Alert",
        replace_existing=True,
    )

    # Daily at 9:00 AM PT: rental listings ingest + alert
    scheduler.add_job(
        run_rental_pipeline,
        trigger=CronTrigger(hour=9, minute=0, timezone="America/Los_Angeles"),
        id="rental_pipeline",
        name="Rental Ingest + Score + Alert",
        replace_existing=True,
    )

    # Every day at 8:00 AM PT: daily report
    scheduler.add_job(
        run_daily_report,
        trigger=CronTrigger(hour=8, minute=0, timezone="America/Los_Angeles"),
        id="daily_report",
        name="Daily Report",
        replace_existing=True,
    )

    # Every 30 minutes: CRM follow-up check
    scheduler.add_job(
        run_crm_check,
        trigger=IntervalTrigger(minutes=30),
        id="crm_check",
        name="CRM Follow-up Check",
        replace_existing=True,
    )

    logger.info("Scheduler started. Jobs: sales (4h), rentals (9am), report (8am), crm (30m)")
    logger.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")
        scheduler.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Property Bot Scheduler")
    parser.add_argument("--once", action="store_true", help="Run both pipelines once then exit")
    parser.add_argument("--sales", action="store_true", help="Run for-sale pipeline only")
    parser.add_argument("--rentals", action="store_true", help="Run rental pipeline only")
    args = parser.parse_args()

    if args.sales:
        logger.info("Running FOR-SALE pipeline...")
        run_ingest_pipeline()
    elif args.rentals:
        logger.info("Running RENTAL pipeline...")
        run_rental_pipeline()
    elif args.once:
        logger.info("Running both pipelines...")
        run_ingest_pipeline()
        run_rental_pipeline()
        run_daily_report()
    else:
        start_scheduler()
