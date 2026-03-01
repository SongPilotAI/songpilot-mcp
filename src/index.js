#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const TOOL_NAME = "songpilot.orchestrator.run";

const baseUrl =
  process.env.SONGPILOT_MCP_BASE_URL?.replace(/\/$/, "") ||
  "https://dev.songpilot.ai";
const endpoint = `${baseUrl}/mcp/orchestrator/run`;

const apiKey = process.env.SONGPILOT_API_KEY;
const workspaceId = process.env.SONGPILOT_WORKSPACE_ID;

if (!apiKey) {
  console.error("Missing env SONGPILOT_API_KEY (expected sp_...)");
  process.exit(1);
}
if (!workspaceId) {
  console.error("Missing env SONGPILOT_WORKSPACE_ID");
  process.exit(1);
}

let lastSessionId = null;

function asText(result) {
  if (!result) return "";
  if (typeof result === "string") return result;
  return JSON.stringify(result);
}

const server = new Server(
  {
    name: "songpilot-mcp",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: TOOL_NAME,
        description:
          "Run the SongPilot orchestrator for a given workspace. Returns assistant text.",
        inputSchema: {
          type: "object",
          properties: {
            message: { type: "string", description: "User message/prompt" },
            session_id: {
              type: "string",
              description:
                "Optional session id for continuity. If omitted, the server will reuse the last one.",
            },
            context: {
              type: "object",
              description: "Optional structured context object",
              additionalProperties: true,
            },
          },
          required: ["message"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  if (name !== TOOL_NAME) {
    throw new Error(`Unknown tool: ${name}`);
  }

  const message = args?.message;
  if (!message || typeof message !== "string") {
    throw new Error("Missing required argument: message");
  }

  const sessionId =
    (args?.session_id && typeof args.session_id === "string"
      ? args.session_id
      : null) || lastSessionId;

  const body = {
    workspace_id: workspaceId,
    message,
    session_id: sessionId,
    context:
      args?.context && typeof args.context === "object" ? args.context : undefined,
  };

  const resp = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
      "X-MCP-Client": "claude-desktop",
    },
    body: JSON.stringify(body),
  });

  const text = await resp.text();
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${text}`);
  }

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Invalid JSON from server: ${text.slice(0, 500)}`);
  }

  if (data?.session_id) lastSessionId = data.session_id;

  const outText = asText(data?.text);

  return {
    content: [{ type: "text", text: outText }],
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
