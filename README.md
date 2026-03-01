# songpilot-mcp

MCP stdio server for SongPilot.

## Requirements

- Node.js 18+ (Node 20+ recommended)
- A SongPilot API key (`sp_...`)
- A SongPilot workspace id

## Environment

- `SONGPILOT_API_KEY` (required)
- `SONGPILOT_WORKSPACE_ID` (required)
- `SONGPILOT_MCP_BASE_URL` (optional, default: `https://dev.songpilot.ai`)

## Run locally

```bash
cd songpilot-mcp
npm install
SONGPILOT_API_KEY=sp_... \
SONGPILOT_WORKSPACE_ID=... \
npm start
```

## Claude Desktop config (minimal)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "songpilot": {
      "command": "node",
      "args": ["/ABS/PATH/TO/SongPilotAI/songpilot-mcp/src/index.js"],
      "env": {
        "SONGPILOT_API_KEY": "sp_...",
        "SONGPILOT_WORKSPACE_ID": "...",
        "SONGPILOT_MCP_BASE_URL": "https://dev.songpilot.ai"
      }
    }
  }
}
```
