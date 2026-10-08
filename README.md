# songpilot-mcp (archived)

This adapter is retired. SongPilot now runs a hosted MCP server, so there is
nothing to install.

To connect Claude, add a custom connector with this URL and sign in to
SongPilot:

```
https://app.songpilot.ai/agents/mcp
```

Claude Code:

```bash
claude mcp add --transport http songpilot https://app.songpilot.ai/agents/mcp
```

Setup: https://songpilot.ai/mcp
