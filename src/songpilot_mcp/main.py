"""FastMCP server for SongPilot - main entry point.

This module implements the Model Context Protocol (MCP) server that enables
Claude Desktop and other MCP clients to interact with SongPilot's AI agents.

Architecture:
-----------
- Stdio transport: Runs locally on user's machine, communicates via stdin/stdout
- HTTP client: Makes API calls to songpilot-agents service
- Tool-based interface: Exposes orchestrator.run for all interactions

Deployment:
-----------
- Client-side package (not server-side)
- Users install via pip: pip install songpilot-mcp
- Claude Desktop spawns the process and communicates via stdio
- No Docker/Kubernetes needed - runs on user's local machine
"""

import sys
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from songpilot_mcp.client import SongPilotError, get_client
from songpilot_mcp.config import get_settings
from songpilot_mcp.logging_config import get_logger, setup_logging

# Initialize logger
logger = get_logger(__name__)

# Create FastMCP server instance
# Name shown in Claude Desktop and other MCP clients
mcp = FastMCP(
    "songpilot",
    instructions="""
    SongPilot AI - Your music career co-pilot.

    This MCP server connects Claude to SongPilot's AI agent system, enabling:
    - Artwork generation for songs, albums, and profiles
    - Release planning and strategy
    - Artist profile creation
    - Content writing for social media
    - Career management advice

    Use the run_orchestrator tool to interact with SongPilot's AI agents.
    """,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring and readiness probes."""
    return JSONResponse(
        {
            "status": "healthy",
            "service": "songpilot-mcp",
            "version": "0.2.0",
        }
    )


@mcp.tool()
async def run_orchestrator(
    message: str,
    session_id: str | None = None,
    context: dict[str, Any] | None = None,
    ctx: Context = None,
) -> str:
    """
    Run the SongPilot orchestrator to interact with AI agents.

    This is the primary interface for interacting with SongPilot's AI system.
    The orchestrator routes your requests to appropriate specialists
    (visual-director, manager, publicist, etc.) based on your needs.

    Args:
        message: Your request or question for the SongPilot AI.
                Examples:
                - "Create artwork for my song 'Midnight Dreams'"
                - "Help me plan a release strategy for my new album"
                - "Write a bio for my artist profile"
                - "Which of my songs are ready for release?"

        session_id: Optional session identifier for conversation continuity.
                   If omitted, the server maintains session continuity automatically.
                   Use this if you want to explicitly reference a previous conversation.

        context: Optional context about your current activity.
                Providing context helps the AI give more relevant responses:
                {
                    "currentPage": "/songs",
                    "activeTab": "albums",
                    "focusedResource": {"type": "album", "name": "My Album"}
                }

        ctx: FastMCP context (auto-injected, used for logging).

    Returns:
        The AI's response as text. This may include suggestions, questions,
        generated content, or action items depending on your request.

    Examples:
        >>> result = await run_orchestrator("Create artwork for my song 'Midnight Dreams'")
        >>> print(result)
        "I'd be happy to help create artwork for 'Midnight Dreams'!
         What style are you envisioning? Minimal, artistic, or something else?"

        >>> # Continue conversation with context
        >>> result = await run_orchestrator(
        ...     "Make it minimal with blue tones",
        ...     context={"currentPage": "/songs", "activeTab": "singles"}
        ... )

    Raises:
        SongPilotError: If the API call fails (network error, auth error, etc.)

    Note:
        - Session continuity is maintained automatically within a Claude conversation
        - The orchestrator remembers context from previous messages
        - API calls may take 10-30 seconds for complex generation tasks
    """
    if ctx:
        await ctx.info(f"Orchestrator request: {message[:50]}...")

    logger.info(
        "Running orchestrator",
        message_preview=message[:100],
        has_session=bool(session_id),
        has_context=bool(context),
    )

    try:
        client = get_client()
        result = await client.run_orchestrator(
            message=message,
            session_id=session_id,
            context=context,
        )

        response_text = result.get("text", "")

        logger.info(
            "Orchestrator response received",
            response_length=len(response_text),
            session_id=result.get("session_id"),
        )

        return response_text

    except SongPilotError as e:
        logger.error(
            "SongPilot API error",
            error=str(e),
            status_code=e.status_code,
        )

        error_message = f"Error communicating with SongPilot: {e}"
        if e.status_code == 401:
            error_message = (
                "Authentication failed. Please check your SONGPILOT_API_KEY."
            )
        elif e.status_code == 404:
            error_message = (
                "Workspace not found. Please check your SONGPILOT_WORKSPACE_ID."
            )
        elif e.status_code and e.status_code >= 500:
            error_message = (
                "SongPilot service temporarily unavailable. Please try again later."
            )

        if ctx:
            await ctx.error(error_message)

        return error_message

    except Exception as e:
        logger.exception("Unexpected error in run_orchestrator")
        error_message = f"An unexpected error occurred: {str(e)}"

        if ctx:
            await ctx.error(error_message)

        return error_message


def main() -> None:
    """Entry point for the MCP server.

    This function is called when users run:
    - python -m songpilot_mcp
    - songpilot-mcp (console script)

    It:
    1. Loads configuration from environment
    2. Sets up logging
    3. Starts the FastMCP server with stdio transport
    """
    settings = get_settings()

    # Configure logging
    setup_logging(settings.log_level)

    logger.info(
        "Starting SongPilot MCP server",
        version="0.2.0",
        workspace_id=settings.workspace_id,
        base_url=settings.base_url,
    )

    print(
        f"SongPilot MCP Server v0.2.0\n"
        f"Workspace: {settings.workspace_id}\n"
        f"Ready for Claude Desktop...",
        file=sys.stderr,
    )

    # Run with stdio transport (for Claude Desktop, Cursor, etc.)
    # This blocks and handles the MCP protocol over stdin/stdout
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()