"""Structured logging configuration with Sentry integration."""

import logging
import sys

import sentry_sdk
import structlog
from sentry_sdk.integrations.logging import LoggingIntegration

from songpilot_mcp.config import get_settings


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with Sentry integration.

    This sets up:
    1. Structlog for structured JSON logging
    2. Sentry for error tracking (if DSN configured)
    3. Console handler with appropriate formatting

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    settings = get_settings()

    # Configure Sentry if DSN provided
    if settings.sentry_dsn:
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[sentry_logging],
            traces_sample_rate=0.1,  # 10% sampling for performance
            environment="production",
            release=f"songpilot-mcp@{getattr(settings, 'version', '0.2.0')}",
        )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Quiet noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structlog logger instance
    """
    return structlog.get_logger(name)
