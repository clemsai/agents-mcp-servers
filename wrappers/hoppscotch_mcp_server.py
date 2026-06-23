# Hoppscotch MCP Server — API client for AI agents
# Wraps Hoppscotch collections: execute REST/GraphQL requests, manage collections
# Monetization: $29/mo hosted, x402 pay-per-request

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("hoppscotch-mcp-server")

HOPPSCOTCH_URL = os.environ.get("HOPPSCOTCH_URL", "http://localhost:3000")
HOPPSCOTCH_TOKEN = os.environ.get("HOPPSCOTCH_TOKEN", "")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="http_request",
            description="Execute an HTTP request (REST API call). Supports GET, POST, PUT, DELETE, PATCH.",
            inputSchema={
                "type": "object",
                "required": ["url", "method"],
                "properties": {
                    "url": {"type": "string", "description": "Request URL"},
                    "method": {"type": "string", "description": "HTTP method (GET, POST, PUT, DELETE, PATCH)"},
                    "headers": {"type": "object", "description": "Request headers"},
                    "body": {"type": "string", "description": "Request body (JSON string)"},
                    "params": {"type": "object", "description": "Query parameters"}
                }
            }
        ),
        Tool(
            name="graphql_query",
            description="Execute a GraphQL query against an endpoint",
            inputSchema={
                "type": "object",
                "required": ["url", "query"],
                "properties": {
                    "url": {"type": "string", "description": "GraphQL endpoint URL"},
                    "query": {"type": "string", "description": "GraphQL query string"},
                    "variables": {"type": "object", "description": "Query variables"},
                    "headers": {"type": "object", "description": "Request headers"}
                }
            }
        ),
        Tool(
            name="list_collections",
            description="List Hoppscotch collections",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="run_collection",
            description="Run all requests in a Hoppscotch collection",
            inputSchema={
                "type": "object",
                "required": ["collection_id"],
                "properties": {
                    "collection_id": {"type": "string", "description": "Collection ID"},
                    "environment": {"type": "object", "description": "Environment variables"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    headers = {"Authorization": f"Bearer {HOPPSCOTCH_TOKEN}"} if HOPPSCOTCH_TOKEN else {}
    
    try:
        async with httpx.AsyncClient(base_url=HOPPSCOTCH_URL, headers=headers, timeout=30) as client:
            if name == "http_request":
                url = arguments["url"]
                method = arguments["method"].upper()
                req_headers = arguments.get("headers", {})
                body = arguments.get("body", "")
                params = arguments.get("params", {})
                
                r = await client.request(
                    method=method,
                    url=url,
                    headers=req_headers,
                    content=body.encode() if body else None,
                    params=params
                )
                result = {
                    "status": r.status_code,
                    "headers": dict(r.headers),
                    "body": r.text[:5000]
                }
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "graphql_query":
                url = arguments["url"]
                payload = {
                    "query": arguments["query"],
                    "variables": arguments.get("variables", {})
                }
                req_headers = {"Content-Type": "application/json"}
                if "headers" in arguments:
                    req_headers.update(arguments["headers"])
                r = await client.post(url, json=payload, headers=req_headers)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "list_collections":
                r = await client.get("/api/collections")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "run_collection":
                col_id = arguments["collection_id"]
                env = arguments.get("environment", {})
                r = await client.get(f"/api/collections/{col_id}")
                r.raise_for_status()
                collection = r.json()
                results = []
                for req in collection.get("requests", []):
                    try:
                        r2 = await client.request(
                            method=req.get("method", "GET"),
                            url=req.get("url", ""),
                            headers={h["key"]: h["value"] for h in req.get("headers", []) if h.get("enabled", True)},
                            content=req.get("body", "").encode() if req.get("body") else None
                        )
                        results.append({"name": req.get("name", ""), "status": r2.status_code, "body": r2.text[:1000]})
                    except Exception as e:
                        results.append({"name": req.get("name", ""), "error": str(e)})
                return [TextContent(type="text", text=json.dumps(results, indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
