"""
Central logging configuration — import early to set up once.
"""

import logging
import sys


def setup_logging(log_file: str = "bot.log") -> None:
    """Configure root logger with console + file handlers."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, mode="a", encoding="utf-8"),
        ],
    )
    # Suppress noisy library logs
    for name in ("httpx", "httpcore", "sqlalchemy.engine", "apscheduler"):
        logging.getLogger(name).setLevel(logging.WARNING)
