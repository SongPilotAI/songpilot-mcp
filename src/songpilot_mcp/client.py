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


class ApiError(SongPilotError):
    """A SongPilot API call failed. The message is ours, never the response body."""


# Short messages for API failures. Response bodies are never passed through, so
# no upstream wording reaches the MCP caller.
_STATUS_MESSAGES = {
    400: "SongPilot could not accept that request. Check the values and try again.",
    401: "Authentication failed. Check SONGPILOT_API_KEY.",
    402: "This workspace needs an active plan or more credits for that.",
    403: "This API key is not allowed to do that in this workspace.",
    404: "Not found in this workspace.",
    409: "That conflicts with existing data, for example it is already linked.",
    422: "SongPilot could not accept that request. Check the values and try again.",
    429: "Too many requests. Wait a moment and try again.",
}


def _error_message(status_code: int, overrides: dict[int, str] | None) -> str:
    if overrides and status_code in overrides:
        return overrides[status_code]
    if status_code in _STATUS_MESSAGES:
        return _STATUS_MESSAGES[status_code]
    if 300 <= status_code < 400:
        return (
            "SongPilot redirected the request to a sign-in page. "
            "Check SONGPILOT_MCP_BASE_URL and CF_ACCESS_TOKEN."
        )
    if status_code >= 500:
        return "SongPilot is temporarily unavailable. Please try again later."
    return f"SongPilot returned an error ({status_code})."


class SongPilotClient:
    """HTTP client for SongPilot API.

    This client handles communication with the SongPilot orchestrator
    endpoint and the SongPilot API. It manages:
    - Authentication (Bearer token)
    - Session continuity
    - Error handling
    - Request/response logging
    """

    def __init__(self) -> None:
        """Initialize client with settings."""
        self.settings = get_settings()
        self._last_session_id: str | None = None

    def _auth_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.settings.effective_api_key}",
            "X-Workspace-Id": self.settings.workspace_id,
        }
        if self.settings.cf_access_token:
            headers["cf-access-token"] = self.settings.cf_access_token
        return headers

    async def api_request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        errors: dict[int, str] | None = None,
    ) -> Any:
        """Call the SongPilot API and return the unwrapped response data.

        The workspace travels in the X-Workspace-Id header, never in the path.

        Args:
            method: HTTP method
            path: API path starting with /api/
            json: Optional JSON body
            params: Optional query parameters; None values are dropped
            errors: Optional per-status messages that replace the defaults

        Raises:
            ApiError: With a short message of our own on any failure
        """
        if not path.startswith("/api/"):
            raise ValueError(f"API path must start with /api/: {path}")

        url = f"{self.settings.base_url.rstrip('/')}{path}"
        query = {k: v for k, v in (params or {}).items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.request(
                    method,
                    url,
                    json=json,
                    params=query or None,
                    headers=self._auth_headers(),
                )
        except httpx.RequestError as e:
            logger.error("Network error calling API", path=path, error=str(e))
            raise ApiError(
                "Could not reach SongPilot. Check SONGPILOT_MCP_BASE_URL "
                "and your connection."
            ) from e

        status_code = response.status_code
        if not 200 <= status_code < 300:
            logger.error("API error", method=method, path=path, status=status_code)
            raise ApiError(_error_message(status_code, errors), status_code)

        if not response.content:
            return None
        try:
            body = response.json()
        except ValueError as e:
            logger.error("API returned a non-JSON body", path=path)
            raise ApiError(_error_message(502, None), 502) from e

        # Workspace endpoints wrap their data as {success, data, timestamp}.
        if isinstance(body, dict) and "success" in body and "data" in body:
            return body["data"]
        return body

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
            **self._auth_headers(),
            "Content-Type": "application/json",
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
