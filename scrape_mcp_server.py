# Scraping MCP Server — Web scraping for AI agents
# File: /root/agents-mcp-servers/scrape_mcp_server.py

"""
Scraping MCP Server — Web scraping and data extraction for AI agents.

No API key required. Uses httpx + BeautifulSoup.

Tools:
- scrape_url: Extract content from a URL
- extract_links: Extract all links from a URL
- extract_text: Extract clean text from HTML
- extract_table: Extract tables from HTML
"""

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("scrape-mcp-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="scrape_url",
            description="Scrape and extract readable content from a URL. Returns title, text, and metadata.",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"},
                    "max_length": {"type": "integer", "description": "Max text length (default 5000)"}
                }
            }
        ),
        Tool(
            name="extract_links",
            description="Extract all links from a URL",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "description": "URL to extract links from"}
                }
            }
        ),
        Tool(
            name="extract_emails",
            description="Extract email addresses from a URL or text",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "description": "URL to extract emails from"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    url = arguments.get("url", "")
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MCP-Agent/1.0)"})
            r.raise_for_status()
            
            if name == "scrape_url":
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(r.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.decompose()
                    
                    title = soup.title.string if soup.title else ""
                    text = soup.get_text(separator='\n', strip=True)
                    max_len = arguments.get("max_length", 5000)
                    text = text[:max_len]
                    
                    result = {"title": title, "url": url, "text": text}
                except ImportError:
                    # Fallback without BeautifulSoup
                    result = {"url": url, "text": r.text[:arguments.get("max_length", 5000)]}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "extract_links":
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(r.text, 'html.parser')
                    links = []
                    for a in soup.find_all('a', href=True):
                        links.append({"text": a.get_text(strip=True), "url": a['href']})
                    result = {"url": url, "links": links[:50]}
                except ImportError:
                    import re
                    links = re.findall(r'href="([^"]+)"', r.text)
                    result = {"url": url, "links": links[:50]}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "extract_emails":
                import re
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
                result = {"url": url, "emails": list(set(emails))}
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error scraping {url}: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
