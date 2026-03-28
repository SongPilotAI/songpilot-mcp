"""HTTP client for communicating with SongPilot API."""

from typing import Any

import httpx
import structlog

from songpilot_mcp.config import get_settings

logger = structlog.get_logger("songpilot_mcp.client")


class SongPilotError(Exception):
    """Base exception for SongPilot API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class SongPilotClient:
    """HTTP client for SongPilot API.

    This client handles communication with the SongPilot orchestrator
    endpoint. It manages:
    - Authentication (Bearer token)
    - Session continuity
    - Error handling
    - Request/response logging
    """

    def __init__(self) -> None:
        """Initialize client with settings."""
        self.settings = get_settings()
        self._last_session_id: str | None = None

    async def run_orchestrator(
        self,
        message: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call the SongPilot orchestrator.

        Args:
            message: User message/prompt to send to orchestrator
            session_id: Optional session ID for conversation continuity.
                       If None, uses last session ID if available.
            context: Optional structured context (page, tab, focused resource)

        Returns:
            Response dictionary containing:
            - ok: bool indicating success
            - session_id: str session identifier
            - text: str response text
            - artifacts: list of machine-readable artifacts

        Raises:
            SongPilotError: If API call fails

        Example:
            >>> client = SongPilotClient()
            >>> result = await client.run_orchestrator(
            ...     "Create artwork for my song",
            ...     context={"currentPage": "/songs", "activeTab": "singles"}
            ... )
            >>> print(result["text"])
        """
        # Use provided session_id, last session_id, or generate new
        effective_session_id = session_id or self._last_session_id

        payload = {
            "workspace_id": self.settings.workspace_id,
            "message": message,
            "session_id": effective_session_id,
        }

        # Only include context if provided (not None)
        if context is not None:
            payload["context"] = context

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.effective_api_key}",
            "X-MCP-Client": "claude-desktop",
        }

        endpoint = self.settings.orchestrator_endpoint

        logger.debug(
            "Calling orchestrator",
            endpoint=endpoint,
            workspace_id=self.settings.workspace_id,
            has_session=bool(effective_session_id),
            has_context=bool(context),
        )

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            # API returned error status
            status_code = e.response.status_code
            try:
                body = e.response.text
            except Exception:
                body = None

            logger.error(
                "Orchestrator API error",
                status_code=status_code,
                endpoint=endpoint,
                response_body=body[:500] if body else None,
            )
            raise SongPilotError(
                f"API error {status_code}",
                status_code=status_code,
                response_body=body,
            ) from e

        except httpx.RequestError as e:
            # Network/connection error
            logger.error(
                "Network error calling orchestrator",
                endpoint=endpoint,
                error=str(e),
            )
            raise SongPilotError(
                f"Failed to connect to SongPilot API: {e}",
            ) from e

        except Exception as e:
            # Catch-all for unexpected errors (including test mocking issues)
            logger.error(
                "Unexpected error calling orchestrator",
                endpoint=endpoint,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise SongPilotError(
                f"Failed to connect to SongPilot API: {e}",
            ) from e

        # Store session_id for continuity in subsequent calls
        if data.get("session_id"):
            self._last_session_id = data["session_id"]
            logger.debug(
                "Session updated",
                session_id=self._last_session_id,
            )

        logger.info(
            "Orchestrator call successful",
            session_id=data.get("session_id"),
            response_length=len(data.get("text", "")),
            artifact_count=len(data.get("artifacts", [])),
        )

        return data


# Module-level singleton
_client: SongPilotClient | None = None


def get_client() -> SongPilotClient:
    """Get or create SongPilot client singleton.

    This ensures we reuse the same client instance (and session tracking)
    across multiple tool calls in the same MCP session.

    Returns:
        SongPilotClient singleton instance
    """
    global _client
    if _client is None:
        _client = SongPilotClient()
    return _client
