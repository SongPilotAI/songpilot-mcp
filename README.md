# songpilot-mcp

Turn any MCP-compatible AI tool into a **SongPilot power user**.

This is a minimal MCP stdio server that exposes one tool — `songpilot.orchestrator.run` — which delegates to SongPilot’s Orchestrator (and its specialist agents like Visual Director/Publicist) on your behalf.

## How it works

**Step 1 — Create a SongPilot User API Key**
- In the SongPilot app, go to **Settings → API Keys** (`/settings/api-keys`)
- Create a **User** key (`sp_...`)

**Step 2 — Connect SongPilot to your AI client**
- Configure your MCP client to run this server and pass the API key + workspace id as env vars.

**Step 3 — Ask for outcomes**
Examples:
- “Help me update my artist profile for a release next month.”
- “Review my assets and tell me what’s missing for distribution.”

## Requirements

- Node.js 18+ (Node 20+ recommended)
- A SongPilot API key (`sp_...`)
- A SongPilot workspace id

## Environment

- `SONGPILOT_API_KEY` (required)
- `SONGPILOT_WORKSPACE_ID` (required)
- `SONGPILOT_MCP_BASE_URL` (optional)
  - Local dev: `https://dev.songpilot.ai`
  - Staging: `https://mcp-staging.songpilot.ai` (when available)
  - Production: `https://mcp.songpilot.ai` (when available)

## Run locally

```bash
cd songpilot-mcp
npm install

SONGPILOT_API_KEY=sp_... \
SONGPILOT_WORKSPACE_ID=... \
SONGPILOT_MCP_BASE_URL=https://dev.songpilot.ai \
npm start
```

## Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "songpilot": {
      "command": "node",
      "args": ["/ABS/PATH/TO/songpilot-mcp/src/index.js"],
      "env": {
        "SONGPILOT_API_KEY": "sp_...",
        "SONGPILOT_WORKSPACE_ID": "...",
        "SONGPILOT_MCP_BASE_URL": "https://dev.songpilot.ai"
      }
    }
  }
}
```

## Cursor (MCP)

Cursor supports MCP servers. Configure a new MCP server command pointing at `songpilot-mcp` and set the same env vars:

- `SONGPILOT_API_KEY`
- `SONGPILOT_WORKSPACE_ID`
- `SONGPILOT_MCP_BASE_URL`

(Exact UI steps vary by Cursor version; the core requirement is running this server via stdio with those env vars.)

## Other MCP-compatible clients

Most MCP clients follow the same pattern:

- **Command:** run this server (stdio)
  - `node /ABS/PATH/TO/songpilot-mcp/src/index.js`
- **Environment variables:** provide the SongPilot key + workspace id

If your client supports `npx`, you can also run a checked-out copy of this repo anywhere on disk.

## Security notes

- Treat `sp_...` API keys like passwords.
- Use a dedicated key for each client (e.g. “Claude Desktop”, “Cursor”) so you can revoke independently.
- Some endpoints may be app-only (billing/subscription flows) by design.
