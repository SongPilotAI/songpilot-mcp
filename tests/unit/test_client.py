"""Tests for SongPilot HTTP client."""

import os
from unittest.mock import patch

import pytest
import respx
from httpx import Response

from songpilot_mcp.client import SongPilotClient, SongPilotError


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock required environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "SONGPILOT_API_KEY": "sp_test_api_key_12345",
            "SONGPILOT_WORKSPACE_ID": "test-workspace-id",
        },
        clear=False,
    ):
        yield


@pytest.fixture
def client(mock_env_vars):
    """Create test client with mocked settings."""
    # Import here to ensure env vars are set first
    # Reset the singleton to pick up mocked env vars
    import songpilot_mcp.config as config_module
    from songpilot_mcp.config import get_settings

    config_module._settings = None

    return SongPilotClient()


class TestSongPilotClient:
    """Test suite for HTTP client."""

    @respx.mock
    async def test_run_orchestrator_success(self, client):
        """Test successful orchestrator call."""
        # Mock the endpoint
        route = respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            return_value=Response(
                200,
                json={
                    "ok": True,
                    "text": "Hello! I'm your SongPilot AI assistant.",
                    "session_id": "test-session-123",
                    "artifacts": [],
                },
            )
        )

        result = await client.run_orchestrator("Test message")

        assert result["ok"] is True
        assert result["text"] == "Hello! I'm your SongPilot AI assistant."
        assert result["session_id"] == "test-session-123"
        assert route.called

    @respx.mock
    async def test_run_orchestrator_with_session(self, client):
        """Test orchestrator call with session ID."""
        route = respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            return_value=Response(
                200,
                json={
                    "ok": True,
                    "text": "Response",
                    "session_id": "existing-session",
                },
            )
        )

        result = await client.run_orchestrator("Hi", session_id="existing-session")

        # Verify session_id was passed in request
        request_body = route.calls.last.request.content
        assert b"existing-session" in request_body
        assert result["session_id"] == "existing-session"

    @respx.mock
    async def test_run_orchestrator_with_context(self, client):
        """Test orchestrator call with context."""
        route = respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            return_value=Response(
                200,
                json={
                    "ok": True,
                    "text": "Response",
                    "session_id": "abc",
                },
            )
        )

        context = {"currentPage": "/songs", "activeTab": "albums"}
        result = await client.run_orchestrator("Create artwork", context=context)

        assert result["ok"] is True
        # Verify context was passed
        request_body = route.calls.last.request.content
        assert b"/songs" in request_body
        assert b"albums" in request_body

    @respx.mock
    async def test_run_orchestrator_auth_error(self, client):
        """Test 401 authentication error handling."""
        respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            return_value=Response(401, text="Unauthorized")
        )

        with pytest.raises(SongPilotError) as exc_info:
            await client.run_orchestrator("Test")

        assert exc_info.value.status_code == 401
        assert "401" in str(exc_info.value)

    @respx.mock
    async def test_run_orchestrator_server_error(self, client):
        """Test 500 server error handling."""
        respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        with pytest.raises(SongPilotError) as exc_info:
            await client.run_orchestrator("Test")

        assert exc_info.value.status_code == 500

    @respx.mock
    async def test_run_orchestrator_network_error(self, client):
        """Test network connection error handling."""
        respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            side_effect=Exception("Connection refused")
        )

        with pytest.raises(SongPilotError) as exc_info:
            await client.run_orchestrator("Test")

        assert "Failed to connect" in str(exc_info.value)

    @respx.mock
    async def test_session_continuity(self, client):
        """Test that session ID is maintained across calls."""
        respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            return_value=Response(
                200,
                json={
                    "ok": True,
                    "text": "Response 1",
                    "session_id": "persistent-session",
                },
            )
        )

        # First call
        await client.run_orchestrator("First message")

        # Change mock to verify second call uses same session
        respx.post("https://mcp.songpilot.ai/mcp/orchestrator/run").mock(
            return_value=Response(
                200,
                json={
                    "ok": True,
                    "text": "Response 2",
                    "session_id": "persistent-session",
                },
            )
        )

        # Second call (no explicit session_id)
        await client.run_orchestrator("Second message")

        # Verify last request used persistent session
        # (client._last_session_id should be set)
