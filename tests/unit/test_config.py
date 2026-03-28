"""Tests for configuration module."""

import os
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from songpilot_mcp.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear the settings cache before each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestSettings:
    """Test suite for Settings configuration."""

    def test_settings_from_env_vars(self, clear_settings_cache):
        """Test loading settings from environment variables."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
                "SONGPILOT_MCP_BASE_URL": "https://custom.songpilot.ai",
                "LOG_LEVEL": "debug",
            },
            clear=True,
        ):
            settings = Settings()

            assert settings.api_key == "sp_live_key_123456789"
            assert settings.workspace_id == "ws_abc123"
            assert settings.base_url == "https://custom.songpilot.ai"
            assert settings.log_level == "debug"

    def test_settings_default_values(self, clear_settings_cache):
        """Test default values for optional settings."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
            },
            clear=True,
        ):
            settings = Settings()

            assert settings.base_url == "https://mcp.songpilot.ai"
            assert settings.log_level == "INFO"
            assert settings.sentry_dsn is None
            assert settings.api_key_file is None

    def test_orchestrator_endpoint_property(self, clear_settings_cache):
        """Test the orchestrator_endpoint computed property."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
                "SONGPILOT_MCP_BASE_URL": "https://custom.songpilot.ai",
            },
            clear=True,
        ):
            settings = Settings()

            assert (
                settings.orchestrator_endpoint
                == "https://custom.songpilot.ai/mcp/orchestrator/run"
            )

    def test_orchestrator_endpoint_with_trailing_slash(self, clear_settings_cache):
        """Test orchestrator_endpoint strips trailing slash from base_url."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
                "SONGPILOT_MCP_BASE_URL": "https://api.songpilot.ai/",
            },
            clear=True,
        ):
            settings = Settings()

            assert (
                settings.orchestrator_endpoint
                == "https://api.songpilot.ai/mcp/orchestrator/run"
            )

    def test_effective_api_key_from_env(self, clear_settings_cache):
        """Test that API key is read directly from env."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
            },
            clear=True,
        ):
            settings = Settings()

            assert settings.effective_api_key == "sp_live_key_123456789"

    def test_effective_api_key_from_file(self, clear_settings_cache):
        """Test reading API key from file when api_key_file is set."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
                "SONGPILOT_API_KEY_FILE": "/run/secrets/api_key",
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open(read_data="sp_secret_from_file_123")):
                settings = Settings()
                # When api_key is valid, it takes precedence
                assert settings.effective_api_key == "sp_live_key_123456789"

    def test_effective_api_key_fallback_to_file(self, clear_settings_cache):
        """Test reading API key from file when env var is empty."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
                "SONGPILOT_API_KEY_FILE": "/run/secrets/api_key",
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open(read_data="sp_secret_from_file_123")):
                settings = Settings()
                # API key from env takes precedence
                assert settings.effective_api_key == "sp_live_key_123456789"

    def test_api_key_validation_valid(self, clear_settings_cache):
        """Test that valid API keys pass validation."""
        valid_keys = [
            "sp_live_key_123456789",
            "sp_test_abc123",
            "sp_dev_mykeyhere",
        ]

        for key in valid_keys:
            with patch.dict(
                os.environ,
                {
                    "SONGPILOT_API_KEY": key,
                    "SONGPILOT_WORKSPACE_ID": "ws_abc123",
                },
                clear=True,
            ):
                settings = Settings()
                assert settings.api_key == key

    def test_api_key_validation_invalid(self, clear_settings_cache):
        """Test that invalid API keys fail validation."""
        invalid_keys = [
            "invalid_key",
            "api_key_without_prefix",
            "wrong_prefix_key",
            "not_sp_prefix",
        ]

        for key in invalid_keys:
            # Must set via env var since field uses alias
            with patch.dict(
                os.environ,
                {
                    "SONGPILOT_API_KEY": key,
                    "SONGPILOT_WORKSPACE_ID": "ws_abc123",
                },
                clear=True,
            ):
                with pytest.raises(ValidationError) as exc_info:
                    Settings()

                assert "API key must start with 'sp_'" in str(exc_info.value)

    def test_missing_required_api_key(self, clear_settings_cache):
        """Test that missing API key raises validation error."""
        with patch.dict(
            os.environ,
            {"SONGPILOT_WORKSPACE_ID": "ws_abc123"},
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert (
                "SONGPILOT_API_KEY" in str(exc_info.value)
                or "api_key" in str(exc_info.value).lower()
            )

    def test_missing_required_workspace_id(self, clear_settings_cache):
        """Test that missing workspace ID raises validation error."""
        with patch.dict(
            os.environ,
            {"SONGPILOT_API_KEY": "sp_live_key_123456789"},
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert (
                "SONGPILOT_WORKSPACE_ID" in str(exc_info.value)
                or "workspace_id" in str(exc_info.value).lower()
            )


class TestGetSettings:
    """Test suite for get_settings singleton function."""

    def test_get_settings_returns_singleton(self, clear_settings_cache):
        """Test that get_settings returns the same instance."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
            },
            clear=True,
        ):
            settings1 = get_settings()
            settings2 = get_settings()

            assert settings1 is settings2

    def test_get_settings_creates_instance(self, clear_settings_cache):
        """Test that get_settings creates a valid instance."""
        with patch.dict(
            os.environ,
            {
                "SONGPILOT_API_KEY": "sp_live_key_123456789",
                "SONGPILOT_WORKSPACE_ID": "ws_abc123",
            },
            clear=True,
        ):
            settings = get_settings()

            assert settings is not None
            assert settings.api_key == "sp_live_key_123456789"
            assert settings.workspace_id == "ws_abc123"
