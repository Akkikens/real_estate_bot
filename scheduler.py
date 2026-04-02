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


def run_ingest_pipeline():
    """Main scheduled job: ingest → score → alert."""
    from config import settings
    from database.db import get_db, init_db
    from database.models import Property
    from ingestion.normalizer import upsert_property
    from ingestion.sanity import check as sanity_check, log_anomaly
    from scoring.engine import score_and_update
    from alerts.notifier import check_and_alert

    init_db()

    from ingestion.redfin_adapter import RedfinAdapter
    from ingestion.zillow_adapter import ZillowAdapter
    from ingestion.realtor_adapter import RealtorAdapter
    from ingestion.craigslist_adapter import CraigslistAdapter

    adapters = [
        RedfinAdapter(),
        ZillowAdapter(),
        RealtorAdapter(),
        CraigslistAdapter(),
    ]

    total_new = 0
    with get_db() as db:
        for adapter in adapters:
            logger.info("Ingesting from %s...", adapter.source_name)
            try:
                listings = adapter.fetch_listings(
                    settings.BUYER_TARGET_CITIES,
                    settings.BUYER_MAX_PRICE,
                )
                for normalized in listings:
                    sanity = sanity_check(normalized)
                    if not sanity.passed:
                        log_anomaly(db, normalized, sanity)
                        continue
                    prop, created = upsert_property(db, normalized)
                    score_and_update(prop)
                    if created:
                        total_new += 1
            except Exception as exc:
                logger.error("Adapter %s failed: %s", adapter.source_name, exc)

        props = db.query(Property).filter(
            Property.status == "active",
            Property.is_archived == False,
        ).all()

        n_alerts = check_and_alert(db, props)
        db.commit()

    logger.info("Pipeline complete. New: %d | Alerts sent: %d", total_new, n_alerts)


def run_daily_report():
    """Morning report job."""
    from database.db import get_db, init_db
    from reports.generator import full_report
    import json

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

    # Every 4 hours: full ingest + alert pipeline
    scheduler.add_job(
        run_ingest_pipeline,
        trigger=IntervalTrigger(hours=4),
        id="ingest_pipeline",
        name="Ingest + Score + Alert",
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

    logger.info("Scheduler started. Jobs: ingest (4h), report (8am), crm (30m)")
    logger.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")
        scheduler.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Property Bot Scheduler")
    parser.add_argument("--once", action="store_true", help="Run pipeline once then exit")
    args = parser.parse_args()

    if args.once:
        logger.info("Running single pipeline pass...")
        run_ingest_pipeline()
        run_daily_report()
    else:
        start_scheduler()
