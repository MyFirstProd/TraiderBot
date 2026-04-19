from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(debug: bool = False) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
    ]
    structlog.configure(
        processors=shared + [structlog.processors.JSONRenderer()],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, stream=sys.stdout)


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)
