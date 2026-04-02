#!/usr/bin/env python3
"""
Bay Area Property Acquisition Bot
==================================
Entry point.  All commands are defined in dashboard/cli.py.

Usage:
    python main.py --help
    python main.py run                    # Full pipeline with mock data
    python main.py ingest --source redfin # Pull real listings
    python main.py report                 # Daily digest
    python main.py list --min-score 70    # Filtered property list
    python main.py show "123 Main"        # Full detail + underwriting
    python main.py draft "123 Main"       # Draft agent outreach
    python main.py crm                    # CRM follow-ups
"""

import logging
import sys

# Configure logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", mode="a", encoding="utf-8"),
    ],
)

# Suppress noisy library logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from dashboard.cli import app

if __name__ == "__main__":
    app()
