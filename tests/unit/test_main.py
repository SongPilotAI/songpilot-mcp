"""Tests for SongPilot MCP server main module."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

from songpilot_mcp.client import SongPilotError


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Provide required environment variables for main module tests."""
    with patch.dict(
        os.environ,
        {
            "SONGPILOT_API_KEY": "sp_test_api_key_12345",
            "SONGPILOT_WORKSPACE_ID": "test-workspace-id",
        },
        clear=False,
    ):
        import songpilot_mcp.config as config_module

        config_module._settings = None
        yield
        config_module._settings = None


@pytest.fixture
def mcp_server():
    """Import MCP server after env vars are configured."""
    from songpilot_mcp.main import mcp

    return mcp


class TestToolRegistration:
    """Verify MCP tools are registered with correct schemas."""

    @pytest.mark.asyncio
    async def test_tool_definitions_registered(self, mcp_server):
        tools = await mcp_server.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "run_orchestrator" in tool_names
        assert len(tools) == 1

    @pytest.mark.asyncio
    async def test_run_orchestrator_input_schema(self, mcp_server):
        tools = await mcp_server.list_tools()
        orchestrator_tool = next(t for t in tools if t.name == "run_orchestrator")

        schema = orchestrator_tool.inputSchema
        assert schema["type"] == "object"
        assert "message" in schema["properties"]
        assert "session_id" in schema["properties"]
        assert "context" in schema["properties"]
        assert "message" in schema["required"]


class TestRunOrchestratorTool:
    """Exercise run_orchestrator happy and error paths."""

    @pytest.mark.asyncio
    async def test_run_orchestrator_success(self, mcp_server):
        mock_client = AsyncMock()
        mock_client.run_orchestrator.return_value = {
            "ok": True,
            "text": "Hello from SongPilot!",
            "session_id": "session-abc",
        }

        with patch("songpilot_mcp.main.get_client", return_value=mock_client):
            from songpilot_mcp.main import run_orchestrator

            result = await run_orchestrator("Create artwork for my song")

        assert result == "Hello from SongPilot!"
        mock_client.run_orchestrator.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status_code,expected_fragment",
        [
            (401, "Authentication failed"),
            (404, "Workspace not found"),
            (500, "temporarily unavailable"),
            (None, "Error communicating with SongPilot"),
        ],
    )
    async def test_run_orchestrator_error_response_format(
        self, mcp_server, status_code, expected_fragment
    ):
        mock_client = AsyncMock()
        mock_client.run_orchestrator.side_effect = SongPilotError(
            "API error",
            status_code=status_code,
        )

        with patch("songpilot_mcp.main.get_client", return_value=mock_client):
            from songpilot_mcp.main import run_orchestrator

            result = await run_orchestrator("Test message")

        assert expected_fragment in result

    @pytest.mark.asyncio
    async def test_run_orchestrator_unexpected_error_response_format(self, mcp_server):
        mock_client = AsyncMock()
        mock_client.run_orchestrator.side_effect = RuntimeError("boom")

        with patch("songpilot_mcp.main.get_client", return_value=mock_client):
            from songpilot_mcp.main import run_orchestrator

            result = await run_orchestrator("Test message")

        assert result.startswith("An unexpected error occurred:")


class TestHealthEndpoint:
    """Verify custom health route responds."""

    def test_health_endpoint_responds(self, mcp_server):
        client = TestClient(mcp_server.sse_app())
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "songpilot-mcp"
        assert data["version"] == "0.2.0"


class TestMainEntryPoint:
    """Cover main() startup wiring."""

    def test_main_starts_stdio_transport(self, mock_env_vars):
        mock_settings = MagicMock()
        mock_settings.log_level = "INFO"
        mock_settings.workspace_id = "test-workspace-id"
        mock_settings.base_url = "https://mcp.songpilot.ai"

        with (
            patch("songpilot_mcp.main.get_settings", return_value=mock_settings),
            patch("songpilot_mcp.main.setup_logging") as mock_setup_logging,
            patch("songpilot_mcp.main.mcp.run") as mock_run,
        ):
            from songpilot_mcp.main import main

            main()

        mock_setup_logging.assert_called_once_with("INFO")
        mock_run.assert_called_once_with(transport="stdio")
