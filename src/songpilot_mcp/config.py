"""Configuration management for SongPilot MCP server."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings loaded from environment variables.

    Configuration is loaded from environment variables with support for
    .env files and Docker secrets (via _file suffix pattern).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    base_url: str = Field(
        default="https://mcp.songpilot.ai",
        description="Base URL for SongPilot API endpoints",
        alias="SONGPILOT_MCP_BASE_URL",
    )
    api_key: str = Field(
        description="SongPilot API key (sp_... format)",
        alias="SONGPILOT_API_KEY",
    )
    workspace_id: str = Field(
        description="SongPilot workspace ID",
        alias="SONGPILOT_WORKSPACE_ID",
    )

    # Optional: File-based secrets (Docker secrets support)
    api_key_file: str | None = Field(
        default=None,
        description="Path to file containing API key (Docker secret)",
        alias="SONGPILOT_API_KEY_FILE",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
        alias="LOG_LEVEL",
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Validate API key starts with expected prefix."""
        if not v.startswith("sp_"):
            raise ValueError("API key must start with 'sp_'")
        return v

    @property
    def effective_api_key(self) -> str:
        """Get API key from environment or file.

        Supports Docker secrets pattern where sensitive values can be
        mounted as files (e.g., /run/secrets/api_key).
        """
        # First check direct value
        if self.api_key and self.api_key.strip():
            return self.api_key.strip()

        # Then check file-based secret
        if self.api_key_file:
            try:
                with open(self.api_key_file) as f:
                    key = f.read().strip()
                    if key.startswith("sp_"):
                        return key
            except FileNotFoundError:
                pass

        raise ValueError(
            "No valid API key found. Set SONGPILOT_API_KEY "
            "or SONGPILOT_API_KEY_FILE environment variable."
        )

    @property
    def orchestrator_endpoint(self) -> str:
        """Full URL for orchestrator endpoint."""
        base = self.base_url.rstrip("/")
        return f"{base}/mcp/orchestrator/run"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses LRU cache to avoid re-loading settings on every call.
    Settings are loaded once at startup and cached for the process lifetime.

    Returns:
        Settings instance with validated configuration

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    return Settings()
