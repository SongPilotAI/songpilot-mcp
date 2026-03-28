# SongPilot MCP Server

[![codecov](https://codecov.io/gh/SongPilotAI/songpilot-mcp/graph/badge.svg?token=XUF5YG5EAV)](https://codecov.io/gh/SongPilotAI/songpilot-mcp)

Model Context Protocol (MCP) server for integrating SongPilot AI agents with Claude Desktop and other MCP clients.

## Overview

SongPilot MCP is a client-side package that enables AI assistants like Claude to interact with your SongPilot workspace. It runs locally on your machine and communicates with SongPilot's backend services.

## Installation

### From PyPI (Recommended)

```bash
pip install songpilot-mcp
```

### From Source

```bash
git clone https://github.com/songpilotai/songpilot-mcp.git
cd songpilot-mcp
pip install -r requirements.txt
pip install -e .
```

## Configuration

Create a `.env` file in your working directory:

```bash
SONGPILOT_API_KEY=sp_your_api_key_here
SONGPILOT_WORKSPACE_ID=your_workspace_id
SONGPILOT_MCP_BASE_URL=https://mcp.songpilot.ai
```

Or set environment variables directly:

```bash
export SONGPILOT_API_KEY=sp_your_api_key_here
export SONGPILOT_WORKSPACE_ID=your_workspace_id
```

### Getting Your API Key

1. Log into your SongPilot account
2. Go to Settings > API Keys
3. Generate a new key (format: `sp_...`)
4. Copy your workspace ID from the URL or settings page

## Usage with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "songpilot": {
      "command": "songpilot-mcp",
      "env": {
        "SONGPILOT_API_KEY": "sp_your_api_key",
        "SONGPILOT_WORKSPACE_ID": "your_workspace_id"
      }
    }
  }
}
```

On macOS, the config file is located at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

On Windows:
`%APPDATA%\Claude\claude_desktop_config.json`

## What You Can Do

Once connected, you can ask Claude to:

- Create artwork for songs and albums
- Plan release strategies
- Write artist bios and social media content
- Analyze your music catalog
- Get career management advice

Example prompts:

```
"Create artwork for my song 'Midnight Dreams'"
"Help me plan a release strategy for my new album"
"Write a bio for my artist profile"
"Which of my songs are ready for release?"
```

## Architecture

This is a client-side MCP implementation:

- Runs on your local machine (not on SongPilot servers)
- Communicates via stdio with Claude Desktop
- Makes HTTP API calls to SongPilot services
- No Docker or Kubernetes required

## Development

### Setup

```bash
make venv          # Create virtual environment
make install-dev   # Install dependencies
```

### Commands

```bash
make format        # Format code with black and isort
make lint          # Run ruff linter and format checks
make test          # Run pytest with coverage
make build         # Build package for distribution
make publish       # Publish to PyPI (requires token)
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=songpilot_mcp --cov-report=html

# Specific test file
pytest tests/unit/test_client.py -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SONGPILOT_API_KEY` | Yes | - | Your SongPilot API key (sp_...) |
| `SONGPILOT_WORKSPACE_ID` | Yes | - | Your workspace ID |
| `SONGPILOT_MCP_BASE_URL` | No | `https://mcp.songpilot.ai` | API base URL |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `SENTRY_DSN` | No | - | Sentry DSN for error tracking |

## Troubleshooting

### "Authentication failed"

- Verify your API key starts with `sp_`
- Check that the key is active in your SongPilot settings
- Ensure the workspace ID is correct

### "Workspace not found"

- Confirm you're using the correct workspace ID
- Verify you have access to the workspace

### Connection issues

- Check your internet connection
- Verify `SONGPILOT_MCP_BASE_URL` is correct (default: https://mcp.songpilot.ai)
- Check SongPilot status page for service outages

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://docs.songpilot.ai
- Issues: https://github.com/songpilotai/songpilot-mcp/issues
- Email: support@songpilot.ai

## Changelog

### 0.2.0

- Migrated from Node.js to Python
- Added FastMCP framework support
- Improved error handling and logging
- Added Sentry integration
- Comprehensive test coverage

### 0.1.0

- Initial Node.js implementation
- Basic orchestrator integration
- Stdio transport for Claude Desktop
