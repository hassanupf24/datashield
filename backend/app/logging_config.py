"""
DATASHIELD Structured Logging Configuration
Production-grade logging with structured JSON output, trace correlation,
and security event tagging.
"""
from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

# Context variable for request-scoped trace IDs
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="no-trace")
user_id_var: ContextVar[str] = ContextVar("user_id", default="anonymous")


def add_trace_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Inject trace ID and user ID into every log entry."""
    event_dict["trace_id"] = trace_id_var.get()
    event_dict["user_id"] = user_id_var.get()
    return event_dict


def add_service_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Inject service metadata into every log entry."""
    event_dict["service"] = "datashield-backend"
    event_dict["version"] = "1.0.0"
    return event_dict


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Configure structured logging for the entire application.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format - 'json' for production, 'console' for development.
    """
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        add_trace_context,
        add_service_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Suppress noisy third-party loggers
    for noisy_logger in ["uvicorn.access", "sqlalchemy.engine", "httpx"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger bound with the given name."""
    return structlog.get_logger(name)


def generate_trace_id() -> str:
    """Generate a unique trace ID for request correlation."""
    return f"trc_{uuid.uuid4().hex[:16]}"
