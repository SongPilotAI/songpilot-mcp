"""Typed MCP tools that call the SongPilot API directly.

Importing this package registers every tool on the shared FastMCP server.
Permissions follow the API key: each call is checked against the role of the
user who created the key.
"""

from songpilot_mcp.tools import catalog, members, releases, videos
