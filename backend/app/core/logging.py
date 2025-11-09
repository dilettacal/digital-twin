#!/usr/bin/env python3
"""Structlog configuration helpers."""

from __future__ import annotations

import logging
import os
from typing import Optional

import structlog


def _get_level_from_env(default: str = "INFO") -> int:
    level_name = os.getenv("LOG_LEVEL", default).upper()
    return getattr(logging, level_name, logging.INFO)


def configure_logging(level: Optional[int] = None) -> None:
    """Configure structlog for the application."""
    if getattr(configure_logging, "_configured", False):
        return

    resolved_level = level if level is not None else _get_level_from_env()

    logging.basicConfig(format="%(message)s", level=resolved_level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
        cache_logger_on_first_use=True,
    )

    structlog.contextvars.clear_contextvars()
    configure_logging._configured = True  # type: ignore[attr-defined]


def get_logger(*args, **kwargs) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger, ensuring configuration first."""
    configure_logging()
    return structlog.get_logger(*args, **kwargs)
