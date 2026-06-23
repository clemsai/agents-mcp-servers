# Mattermost MCP Server — Team chat for AI agents
# Wraps Mattermost REST API: send messages, manage channels, post files
# Monetization: $29/mo hosted, x402 pay-per-message

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("mattermost-mcp-server")

MM_URL = os.environ.get("MATTERMOST_URL", "http://localhost:8065")
MM_TOKEN = os.environ.get("MATTERMOST_TOKEN", "")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_channels",
            description="List all channels the bot has access to",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="send_message",
            description="Send a message to a channel",
            inputSchema={
                "type": "object",
                "required": ["channel_id", "message"],
                "properties": {
                    "channel_id": {"type": "string", "description": "Channel ID"},
                    "message": {"type": "string", "description": "Message text (supports Markdown)"},
                    "root_id": {"type": "string", "description": "Thread parent message ID (optional)"}
                }
            }
        ),
        Tool(
            name="get_messages",
            description="Get recent messages from a channel",
            inputSchema={
                "type": "object",
                "required": ["channel_id"],
                "properties": {
                    "channel_id": {"type": "string", "description": "Channel ID"},
                    "limit": {"type": "integer", "description": "Max messages (default 20)"},
                    "before": {"type": "string", "description": "Get messages before this message ID"}
                }
            }
        ),
        Tool(
            name="create_channel",
            description="Create a new channel",
            inputSchema={
                "type": "object",
                "required": ["name", "display_name"],
                "properties": {
                    "name": {"type": "string", "description": "Channel name (URL-safe)"},
                    "display_name": {"type": "string", "description": "Display name"},
                    "purpose": {"type": "string", "description": "Channel purpose"},
                    "private": {"type": "boolean", "description": "Private channel (default false)"}
                }
            }
        ),
        Tool(
            name="send_direct_message",
            description="Send a direct message to a user",
            inputSchema={
                "type": "object",
                "required": ["user_id", "message"],
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "message": {"type": "string", "description": "Message text"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    headers = {"Authorization": f"Bearer {MM_TOKEN}"} if MM_TOKEN else {}
    
    try:
        async with httpx.AsyncClient(base_url=MM_URL, headers=headers, timeout=15) as client:
            if name == "list_channels":
                r = await client.get("/api/v4/channels")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "send_message":
                payload = {
                    "channel_id": arguments["channel_id"],
                    "message": arguments["message"]
                }
                if "root_id" in arguments:
                    payload["root_id"] = arguments["root_id"]
                r = await client.post("/api/v4/posts", json=payload)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "get_messages":
                channel_id = arguments["channel_id"]
                params = {"limit": arguments.get("limit", 20)}
                if "before" in arguments:
                    params["before"] = arguments["before"]
                r = await client.get(f"/api/v4/channels/{channel_id}/posts", params=params)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "create_channel":
                payload = {
                    "name": arguments["name"],
                    "display_name": arguments["display_name"],
                    "team_id": arguments.get("team_id", ""),
                    "purpose": arguments.get("purpose", ""),
                    "private": arguments.get("private", False)
                }
                r = await client.post("/api/v4/channels", json=payload)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "send_direct_message":
                user_id = arguments["user_id"]
                # Create direct message channel first
                r = await client.post("/api/v4/channels/direct", json=[user_id, "me"])
                r.raise_for_status()
                channel_id = r.json()["id"]
                # Send message
                payload = {"channel_id": channel_id, "message": arguments["message"]}
                r2 = await client.post("/api/v4/posts", json=payload)
                r2.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r2.json(), indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
