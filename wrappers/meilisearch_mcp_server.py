# Meilisearch MCP Server - Instant search for AI agents
import os, json, asyncio, httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("meilisearch-mcp-server")
MEILI_URL = os.environ.get("MEILI_URL", "http://localhost:7700")
MEILI_API_KEY = os.environ.get("MEILI_API_KEY", "")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="list_indexes", description="List all indexes",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="create_index", description="Create a search index",
             inputSchema={"type": "object", "required": ["index_name"],
                 "properties": {"index_name": {"type": "string"}, "primary_key": {"type": "string"}}}),
        Tool(name="add_documents", description="Add documents to index",
             inputSchema={"type": "object", "required": ["index_name", "documents"],
                 "properties": {"index_name": {"type": "string"},
                     "documents": {"type": "array", "items": {"type": "object"}}}}),
        Tool(name="search", description="Search an index",
             inputSchema={"type": "object", "required": ["index_name", "query"],
                 "properties": {"index_name": {"type": "string"}, "query": {"type": "string"},
                     "limit": {"type": "integer"}}}),
        Tool(name="get_document", description="Get document by ID",
             inputSchema={"type": "object", "required": ["index_name", "document_id"],
                 "properties": {"index_name": {"type": "string"}, "document_id": {"type": "string"}}}),
        Tool(name="delete_index", description="Delete an index",
             inputSchema={"type": "object", "required": ["index_name"],
                 "properties": {"index_name": {"type": "string"}}}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    headers = {"Authorization": "Bearer " + MEILI_API_KEY} if MEILI_API_KEY else {}
    try:
        async with httpx.AsyncClient(base_url=MEILI_URL, headers=headers, timeout=15) as c:
            if name == "list_indexes":
                r = await c.get("/indexes")
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "create_index":
                payload = {}
                if "primary_key" in arguments: payload["primaryKey"] = arguments["primary_key"]
                r = await c.post("/indexes/" + arguments["index_name"], json=payload)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "add_documents":
                r = await c.post("/indexes/" + arguments["index_name"] + "/documents",
                    json=arguments["documents"])
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "search":
                payload = {"q": arguments["query"], "limit": arguments.get("limit", 20)}
                r = await c.post("/indexes/" + arguments["index_name"] + "/search", json=payload)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "get_document":
                r = await c.get("/indexes/" + arguments["index_name"] + "/documents/" + arguments["document_id"])
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "delete_index":
                r = await c.delete("/indexes/" + arguments["index_name"])
                return [TextContent(type="text", text=json.dumps({"deleted": True}))]
            else:
                return [TextContent(type="text", text=f"Unknown: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    async with stdio_server() as (rs, ws):
        await server.run(rs, ws, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
