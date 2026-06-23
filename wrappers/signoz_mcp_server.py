# SigNoz MCP Server - Observability for AI agents
import os, json, asyncio, httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("signoz-mcp-server")
SIGNOZ_URL = os.environ.get("SIGNOZ_URL", "http://localhost:3301")
SIGNOZ_API_KEY = os.environ.get("SIGNOZ_API_KEY", "")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="query_metrics", description="Query Prometheus metrics",
             inputSchema={"type": "object", "required": ["query"],
                 "properties": {"query": {"type": "string"}, "step": {"type": "string"}}}),
        Tool(name="list_services", description="List instrumented services",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="get_traces", description="Get traces for a service",
             inputSchema={"type": "object", "required": ["service_name"],
                 "properties": {"service_name": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="query_logs", description="Query logs",
             inputSchema={"type": "object", "required": ["query"],
                 "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}}),
        Tool(name="get_service_health", description="Get service health",
             inputSchema={"type": "object", "required": ["service_name"],
                 "properties": {"service_name": {"type": "string"}, "window": {"type": "string"}}}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    headers = {"Authorization": "Bearer " + SIGNOZ_API_KEY} if SIGNOZ_API_KEY else {}
    try:
        async with httpx.AsyncClient(base_url=SIGNOZ_URL, headers=headers, timeout=15) as c:
            if name == "query_metrics":
                payload = {"query": arguments["query"]}
                if "step" in arguments: payload["step"] = arguments["step"]
                r = await c.post("/api/v4/query_range", json=payload)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "list_services":
                r = await c.get("/api/v4/services")
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "get_traces":
                params = {"service": arguments["service_name"], "limit": arguments.get("limit", 10)}
                r = await c.get("/api/v4/traces", params=params)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "query_logs":
                payload = {"query": arguments["query"], "limit": arguments.get("limit", 20)}
                r = await c.post("/api/v4/query_logs", json=payload)
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            elif name == "get_service_health":
                svc = arguments["service_name"]
                window = arguments.get("window", "5m")
                results = {}
                for mname, query in {
                    "throughput": 'rate(http_requests_total{service="' + svc + '"}[' + window + '])',
                    "error_rate": 'rate(http_requests_total{service="' + svc + '",status=~"5.."}[' + window + ']) / rate(http_requests_total{service="' + svc + '"}[' + window + '])'
                }.items():
                    r = await c.post("/api/v4/query_range", json={"query": query, "step": window})
                    results[mname] = r.json() if r.status_code == 200 else r.text
                return [TextContent(type="text", text=json.dumps(results, indent=2))]
            else:
                return [TextContent(type="text", text=f"Unknown: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    async with stdio_server() as (rs, ws):
        await server.run(rs, ws, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
