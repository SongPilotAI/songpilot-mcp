"""The FastMCP server instance shared by main.py and the typed tools."""

from mcp.server.fastmcp import FastMCP

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
    Use the typed tools (list_songs, update_song, create_release, ...) to read
    and change songs, albums, members, releases, music videos, templates and
    social accounts directly.
    """,
)
