# Plane MCP Server — Project management for AI agents
# Wraps Plane REST API: create issues, manage projects, update cycles
# Monetization: $29/mo hosted, x402 pay-per-action

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("plane-mcp-server")

PLANE_URL = os.environ.get("PLANE_URL", "http://localhost:8000")
PLANE_API_KEY = os.environ.get("PLANE_API_KEY", "")
PLANE_WORKSPACE = os.environ.get("PLANE_WORKSPACE", "")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_projects",
            description="List all projects in the workspace",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="create_issue",
            description="Create a new issue in a project",
            inputSchema={
                "type": "object",
                "required": ["project_id", "name"],
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "name": {"type": "string", "description": "Issue title"},
                    "description": {"type": "string", "description": "Issue description"},
                    "priority": {"type": "string", "description": "Priority: urgent, high, medium, low, none"},
                    "state": {"type": "string", "description": "State: backlog, todo, in_progress, done, cancelled"},
                    "assignees": {"type": "array", "items": {"type": "string"}, "description": "User IDs to assign"}
                }
            }
        ),
        Tool(
            name="list_issues",
            description="List issues in a project with filters",
            inputSchema={
                "type": "object",
                "required": ["project_id"],
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "state": {"type": "string", "description": "Filter by state"},
                    "priority": {"type": "string", "description": "Filter by priority"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"}
                }
            }
        ),
        Tool(
            name="update_issue",
            description="Update an existing issue",
            inputSchema={
                "type": "object",
                "required": ["project_id", "issue_id"],
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "issue_id": {"type": "string", "description": "Issue ID"},
                    "name": {"type": "string", "description": "New title"},
                    "description": {"type": "string", "description": "New description"},
                    "priority": {"type": "string", "description": "New priority"},
                    "state": {"type": "string", "description": "New state"}
                }
            }
        ),
        Tool(
            name="add_comment",
            description="Add a comment to an issue",
            inputSchema={
                "type": "object",
                "required": ["project_id", "issue_id", "comment"],
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "issue_id": {"type": "string", "description": "Issue ID"},
                    "comment": {"type": "string", "description": "Comment text"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    headers = {"Authorization": f"Bearer {PLANE_API_KEY}"} if PLANE_API_KEY else {}
    workspace = PLANE_WORKSPACE
    
    try:
        async with httpx.AsyncClient(base_url=PLANE_URL, headers=headers, timeout=15) as client:
            if name == "list_projects":
                r = await client.get(f"/api/v1/workspaces/{workspace}/projects/")
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "create_issue":
                project_id = arguments["project_id"]
                payload = {
                    "name": arguments["name"],
                    "description": arguments.get("description", ""),
                    "priority": arguments.get("priority", "medium"),
                    "state": arguments.get("state", "todo"),
                }
                if "assignees" in arguments:
                    payload["assignees"] = arguments["assignees"]
                r = await client.post(f"/api/v1/workspaces/{workspace}/projects/{project_id}/issues/", json=payload)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "list_issues":
                project_id = arguments["project_id"]
                params = {"limit": arguments.get("limit", 20)}
                if "state" in arguments:
                    params["state"] = arguments["state"]
                if "priority" in arguments:
                    params["priority"] = arguments["priority"]
                r = await client.get(f"/api/v1/workspaces/{workspace}/projects/{project_id}/issues/", params=params)
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "update_issue":
                project_id = arguments["project_id"]
                issue_id = arguments["issue_id"]
                payload = {}
                for key in ["name", "description", "priority", "state"]:
                    if key in arguments:
                        payload[key] = arguments[key]
                r = await client.patch(
                    f"/api/v1/workspaces/{workspace}/projects/{project_id}/issues/{issue_id}/",
                    json=payload
                )
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            elif name == "add_comment":
                project_id = arguments["project_id"]
                issue_id = arguments["issue_id"]
                payload = {"comment": arguments["comment"]}
                r = await client.post(
                    f"/api/v1/workspaces/{workspace}/projects/{project_id}/issues/{issue_id}/comments/",
                    json=payload
                )
                r.raise_for_status()
                return [TextContent(type="text", text=json.dumps(r.json(), indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
