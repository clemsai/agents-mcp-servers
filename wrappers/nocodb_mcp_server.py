# NocoDB MCP Server — No-code database for AI agents
# Wraps NocoDB REST API: create tables, query records, manage bases
# Monetization: $29/mo hosted, x402 pay-per-query

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("nocodb-mcp-server")

NOCODB_URL = os.environ.get("NOCODB_URL", "http://localhost:8080")
NOCODB_API_KEY = os.environ.get("NOCODB_API_KEY", "")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_bases",
            description="List all NocoDB bases/databases",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="list_tables",
            description="List tables in a base",
            inputSchema={
                "type": "object",
                "required": ["base_id"],
                "properties": {
                    "base_id": {"type": "string", "description": "Base/project ID"}
                }
            }
        ),
        Tool(
            name="query_records",
            description="Query records from a table with filters",
            inputSchema={
                "type": "object",
                "required": ["base_id", "table_name"],
                "properties": {
                    "base_id": {"type": "string", "description": "Base ID"},
                    "table_name": {"type": "string", "description": "Table name"},
                    "where": {"type": "string", "description": "Filter condition (e.g., '(Name,eq,test)')"},
                    "limit": {"type": "integer", "description": "Max records (default 25)"},
                    "offset": {"type": "integer", "description": "Offset for pagination"}
                }
            }
        ),
        Tool(
            name="create_record",
            description="Create a new record in a table",
            inputSchema={
                "type": "object",
                "required": ["base_id", "table_name", "data"],
                "properties": {
                    "base_id": {"type": "string", "description": "Base ID"},
                    "table_name": {"type": "string", "description": "Table name"},
                    "data": {"type": "object", "description": "Record data as key-value pairs"}
                }
            }
        ),
        Tool(
            name="update_record",
            description="Update an existing record",
            inputSchema={
                "type": "object",
                "required": ["base_id", "table_name", "record_id", "data"],
                "properties": {
                    "base_id": {"type": "string", "description": "Base ID"},
                    "table_name": {"type": "string", "description": "Table name"},
                    "record_id": {"type": "integer", "description": "Record ID"},
                    "data": {"type": "object", "description": "Updated fields"}
                }
            }
        ),
        Tool(
            name="delete_record",
            description="Delete a record from a table",
            inputSchema={
                "type": "object",
                "required": ["base_id", "table_name", "record_id"],
                "properties": {
                    "base_id": {"type": "string", "description": "Base ID"},
                    "table_name": {"type": "string", "description": "Table name"},
                    "record_id": {"type": "integer", "description": "Record ID"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    headers = {"xc-token": NOCODB_API_KEY} if NOCODB_API_KEY else {}
    
    try:
        async with httpx.AsyncClient(base_url=NOCODB_URL, headers=headers, timeout=15) as client:
            if name == "list_bases":
                r = await client.get("/api/v1/db/meta/projects")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "list_tables":
                base_id = arguments["base_id"]
                r = await client.get(f"/api/v1/db/meta/projects/{base_id}/tables")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "query_records":
                base_id = arguments["base_id"]
                table = arguments["table_name"]
                params = {"limit": arguments.get("limit", 25), "offset": arguments.get("offset", 0)}
                if "where" in arguments:
                    params["where"] = arguments["where"]
                r = await client.get(f"/api/v1/db/data/noco/{base_id}/{table}", params=params)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "create_record":
                base_id = arguments["base_id"]
                table = arguments["table_name"]
                data = arguments["data"]
                r = await client.post(f"/api/v1/db/data/noco/{base_id}/{table}", json=data)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "update_record":
                base_id = arguments["base_id"]
                table = arguments["table_name"]
                record_id = arguments["record_id"]
                data = arguments["data"]
                r = await client.patch(f"/api/v1/db/data/noco/{base_id}/{table}/{record_id}", json=data)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "delete_record":
                base_id = arguments["base_id"]
                table = arguments["table_name"]
                record_id = arguments["record_id"]
                r = await client.delete(f"/api/v1/db/data/noco/{base_id}/{table}/{record_id}")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps({"deleted": True, "id": record_id}))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
