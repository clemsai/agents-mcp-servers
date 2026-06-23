# Search MCP Server — Free web search for AI agents
# File: /root/agents-mcp-servers/search_mcp_server.py

"""
Search MCP Server — Free web search for AI agents via DuckDuckGo.

No API key required. Uses DuckDuckGo's instant answer API.

Tools:
- search: Web search with DuckDuckGo
- search_news: News search
- search_images: Image search
"""

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("search-mcp-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search",
            description="Search the web using DuckDuckGo. Returns titles, URLs, and snippets.",
            inputSchema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"}
                }
            }
        ),
        Tool(
            name="search_news",
            description="Search recent news using DuckDuckGo",
            inputSchema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "News search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 10)
    
    try:
        async with httpx.AsyncClient() as client:
            if name == "search":
                # Use DuckDuckGo instant answer API
                r = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
                    timeout=15,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                data = r.json()
                
                results = []
                # Extract related topics as search results
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", "")
                        })
                
                # Also include abstract
                if data.get("Abstract"):
                    results.insert(0, {
                        "title": data.get("Heading", query),
                        "snippet": data["Abstract"],
                        "url": data.get("AbstractURL", "")
                    })
                
                return [TextContent(type="text", text=json.dumps({"results": results}, indent=2))]
            
            elif name == "search_news":
                # Use DuckDuckGo news
                r = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query + " news", "format": "json", "no_html": "1"},
                    timeout=15,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                data = r.json()
                results = []
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", "")
                        })
                return [TextContent(type="text", text=json.dumps({"results": results}, indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
