# Ghost MCP Server - Publishing + paid memberships for AI agents
import os, json, asyncio, httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("ghost-mcp-server")
GHOST_URL = os.environ.get("GHOST_URL", "http://localhost:2368")
GHOST_API_KEY = os.environ.get("GHOST_API_KEY", "")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="list_posts", description="List published and draft posts",
             inputSchema={"type": "object", "properties": {
                 "status": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="create_post", description="Create a new blog post",
             inputSchema={"type": "object", "required": ["title", "html"],
                 "properties": {"title": {"type": "string"}, "html": {"type": "string"},
                     "status": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}}),
        Tool(name="list_members", description="List newsletter members",
             inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}}),
        Tool(name="create_member", description="Create a new member",
             inputSchema={"type": "object", "required": ["email"],
                 "properties": {"email": {"type": "string"}, "name": {"type": "string"}}}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    headers = {"Authorization": "Ghost " + GHOST_API_KEY} if GHOST_API_KEY else {}
    try:
        async with httpx.AsyncClient(base_url=GHOST_URL + "/ghost/api/admin", headers=headers, timeout=15) as c:
            if name == "list_posts":
                params = {"limit": arguments.get("limit", 15), "formats": "html"}
                r = await c.get("/posts/", params=params)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "create_post":
                payload = {"posts": [{"title": arguments["title"], "html": arguments["html"],
                    "status": arguments.get("status", "draft")}]}
                if "tags" in arguments:
                    payload["posts"][0]["tags"] = [{"name": t} for t in arguments["tags"]]
                r = await c.post("/posts/", json=payload)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "list_members":
                r = await c.get("/members/", params={"limit": arguments.get("limit", 20)})
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "create_member":
                r = await c.post("/members/", json={"members": [{
                    "email": arguments["email"], "name": arguments.get("name", "")}]})
                r.raise_for_status()
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
