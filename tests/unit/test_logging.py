"""Tests for logging configuration module."""

import os
from unittest.mock import patch

import structlog

from songpilot_mcp.config import get_settings
from songpilot_mcp.logging_config import get_logger, setup_logging


class TestSetupLogging:
    """Test suite for logging configuration."""

    def test_setup_logging_basic(self):
        """Test that logging can be configured without errors."""
        get_settings.cache_clear()
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
            },
            clear=True,
        ):
            # Should not raise any exceptions
            setup_logging(log_level="INFO")


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a structlog logger."""
        logger = get_logger("test_module")

        assert logger is not None
        # get_logger returns a BoundLoggerLazyProxy, not a BoundLogger directly
        # Calling it or using it as a logger is what matters
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "error")
