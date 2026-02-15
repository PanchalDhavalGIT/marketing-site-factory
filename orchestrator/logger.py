"""Structured logging for the orchestrator and per-site logs."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.config import LOGS_DIR


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def get_main_logger() -> logging.Logger:
    """Get the main orchestrator logger (stdout + file)."""
    logger = logging.getLogger("orchestrator")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler (human-readable)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    ))
    logger.addHandler(console)

    # File handler (JSON lines)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOGS_DIR / "orchestrator.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    return logger


def get_site_logger(slug: str) -> logging.Logger:
    """Get a per-site logger that writes to logs/{slug}.log."""
    logger = logging.getLogger(f"site.{slug}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOGS_DIR / f"{slug}.log")
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger
