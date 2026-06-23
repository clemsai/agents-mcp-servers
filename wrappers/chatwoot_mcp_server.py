# Chatwoot MCP Server - Support desk for AI agents
import os, json, asyncio, httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("chatwoot-mcp-server")
CHATWOOT_URL = os.environ.get("CHATWOOT_URL", "http://localhost:3000")
CHATWOOT_API_KEY = os.environ.get("CHATWOOT_API_KEY", "")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="list_conversations", description="List support conversations",
             inputSchema={"type": "object", "properties": {
                 "status": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="send_message", description="Send a message in a conversation",
             inputSchema={"type": "object", "required": ["conversation_id", "message"],
                 "properties": {"conversation_id": {"type": "integer"}, "message": {"type": "string"},
                     "message_type": {"type": "string"}}}),
        Tool(name="create_contact", description="Create a customer contact",
             inputSchema={"type": "object", "required": ["name", "email"],
                 "properties": {"name": {"type": "string"}, "email": {"type": "string"},
                     "phone": {"type": "string"}}}),
        Tool(name="get_conversation", description="Get conversation details",
             inputSchema={"type": "object", "required": ["conversation_id"],
                 "properties": {"conversation_id": {"type": "integer"}}}),
        Tool(name="update_conversation", description="Update conversation status",
             inputSchema={"type": "object", "required": ["conversation_id"],
                 "properties": {"conversation_id": {"type": "integer"},
                     "status": {"type": "string"}, "assignee_id": {"type": "integer"}}}),
        Tool(name="create_conversation", description="Create new conversation",
             inputSchema={"type": "object", "required": ["contact_id", "message"],
                 "properties": {"contact_id": {"type": "integer"}, "message": {"type": "string"},
                     "inbox_id": {"type": "integer"}}}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    headers = {"api_access_token": CHATWOOT_API_KEY} if CHATWOOT_API_KEY else {}
    try:
        async with httpx.AsyncClient(base_url=CHATWOOT_URL, headers=headers, timeout=15) as c:
            if name == "list_conversations":
                params = {"limit": arguments.get("limit", 20)}
                if "status" in arguments: params["status"] = arguments["status"]
                r = await c.get("/api/v1/conversations", params=params)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "send_message":
                r = await c.post("/api/v1/conversations/" + str(arguments["conversation_id"]) + "/messages",
                    json={"content": arguments["message"], "message_type": arguments.get("message_type", "outgoing")})
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "create_contact":
                payload = {"name": arguments["name"], "email": arguments["email"]}
                if "phone" in arguments: payload["phone_number"] = arguments["phone"]
                r = await c.post("/api/v1/contacts", json=payload)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "get_conversation":
                r = await c.get("/api/v1/conversations/" + str(arguments["conversation_id"]))
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "update_conversation":
                payload = {}
                if "status" in arguments: payload["status"] = arguments["status"]
                if "assignee_id" in arguments: payload["assignee_id"] = arguments["assignee_id"]
                r = await c.patch("/api/v1/conversations/" + str(arguments["conversation_id"]), json=payload)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "create_conversation":
                payload = {"contact_id": arguments["contact_id"],
                    "message": {"content": arguments["message"]}}
                if "inbox_id" in arguments: payload["inbox_id"] = arguments["inbox_id"]
                r = await c.post("/api/v1/conversations", json=payload)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            else:
                return [TextContent(type="text", text=f"Unknown: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    async with stdio_server() as (rs, ws):
        await server.run(rs, ws, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
