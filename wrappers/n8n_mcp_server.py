# n8n MCP Server — Workflow automation for AI agents
# Wraps n8n REST API: trigger workflows, list executions, manage nodes
# Monetization: $29/mo hosted, x402 pay-per-trigger

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("n8n-mcp-server")

NNN_URL = os.environ.get("NNN_URL", "http://localhost:5678")
NNN_API_KEY = os.environ.get("NNN_API_KEY", "")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_workflows",
            description="List all n8n workflows",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="trigger_workflow",
            description="Trigger an n8n workflow by ID or name",
            inputSchema={
                "type": "object",
                "required": ["workflow_id"],
                "properties": {
                    "workflow_id": {"type": "string", "description": "Workflow ID or name"},
                    "data": {"type": "object", "description": "Input data for the workflow"}
                }
            }
        ),
        Tool(
            name="get_execution",
            description="Get workflow execution status and results",
            inputSchema={
                "type": "object",
                "required": ["execution_id"],
                "properties": {
                    "execution_id": {"type": "string", "description": "Execution ID"}
                }
            }
        ),
        Tool(
            name="list_executions",
            description="List recent workflow executions",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "Filter by workflow ID"},
                    "limit": {"type": "integer", "description": "Max results (default 10)"}
                }
            }
        ),
        Tool(
            name="create_webhook_trigger",
            description="Create a webhook trigger URL for a workflow",
            inputSchema={
                "type": "object",
                "required": ["workflow_name"],
                "properties": {
                    "workflow_name": {"type": "string", "description": "Name for the workflow"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    headers = {"X-N8N-API-KEY": NNN_API_KEY} if NNN_API_KEY else {}
    
    try:
        async with httpx.AsyncClient(base_url=NNN_URL, headers=headers, timeout=15) as client:
            if name == "list_workflows":
                r = await client.get("/api/v1/workflows")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "trigger_workflow":
                wf_id = arguments["workflow_id"]
                data = arguments.get("data", {})
                # Try by name first, then by ID
                r = await client.post(f"/api/v1/workflows/{wf_id}/execute", json=data)
                if r.status_code == 404:
                    # Search by name
                    r2 = await client.get("/api/v1/workflows")
                    for wf in r2.json().get("data", []):
                        if wf["name"] == wf_id:
                            r = await client.post(f"/api/v1/workflows/{wf['id']}/execute", json=data)
                            break
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "get_execution":
                exec_id = arguments["execution_id"]
                r = await client.get(f"/api/v1/executions/{exec_id}")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "list_executions":
                params = {}
                if "workflow_id" in arguments:
                    params["workflowId"] = arguments["workflow_id"]
                params["limit"] = arguments.get("limit", 10)
                r = await client.get("/api/v1/executions", params=params)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "create_webhook_trigger":
                wf_name = arguments["workflow_name"]
                # Create a simple webhook-triggered workflow via API
                workflow_data = {
                    "name": wf_name,
                    "nodes": [
                        {
                            "name": "Webhook",
                            "type": "n8n-nodes-base.webhook",
                            "position": [250, 300],
                            "parameters": {
                                "httpMethod": "POST",
                                "path": wf_name.lower().replace(" ", "-")
                            }
                        }
                    ],
                    "connections": {},
                    "settings": {"executionOrder": "v1"}
                }
                r = await client.post("/api/v1/workflows", json=workflow_data)
                r.raise_for_status()
                wf_id = r.json().get("id", "")
                webhook_url = f"{NNN_URL}/webhook/{wf_name.lower().replace(' ', '-')}"
                return [TextContent(type="text", text=json.dumps({
                    "workflow_id": wf_id,
                    "webhook_url": webhook_url,
                    "message": f"Workflow '{wf_name}' created. POST to {webhook_url} to trigger."
                }, indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
