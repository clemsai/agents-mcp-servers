# Stirling-PDF MCP Server — PDF tools for AI agents
# Wraps Stirling-PDF API: merge, split, convert, OCR, compress PDFs
# Monetization: $29/mo hosted, x402 pay-per-operation

import os
import json
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("stirling-pdf-mcp-server")

STIRLING_URL = os.environ.get("STIRLING_URL", "http://localhost:8080")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="merge_pdfs",
            description="Merge multiple PDFs into one",
            inputSchema={
                "type": "object",
                "required": ["pdf_urls"],
                "properties": {
                    "pdf_urls": {"type": "array", "items": {"type": "string"}, "description": "List of PDF URLs to merge"}
                }
            }
        ),
        Tool(
            name="split_pdf",
            description="Split a PDF into individual pages",
            inputSchema={
                "type": "object",
                "required": ["pdf_url"],
                "properties": {
                    "pdf_url": {"type": "string", "description": "PDF URL to split"},
                    "pages": {"type": "string", "description": "Pages to extract (e.g., '1-3,5,7-9')"}
                }
            }
        ),
        Tool(
            name="pdf_to_images",
            description="Convert PDF pages to images",
            inputSchema={
                "type": "object",
                "required": ["pdf_url"],
                "properties": {
                    "pdf_url": {"type": "string", "description": "PDF URL"},
                    "dpi": {"type": "integer", "description": "Image DPI (default 200)"}
                }
            }
        ),
        Tool(
            name="ocr_pdf",
            description="OCR a PDF to make it searchable",
            inputSchema={
                "type": "object",
                "required": ["pdf_url"],
                "properties": {
                    "pdf_url": {"type": "string", "description": "PDF URL to OCR"},
                    "language": {"type": "string", "description": "OCR language (default 'eng')"}
                }
            }
        ),
        Tool(
            name="compress_pdf",
            description="Compress a PDF to reduce file size",
            inputSchema={
                "type": "object",
                "required": ["pdf_url"],
                "properties": {
                    "pdf_url": {"type": "string", "description": "PDF URL to compress"},
                    "quality": {"type": "string", "description": "Compression quality: low, medium, high"}
                }
            }
        ),
        Tool(
            name="extract_text",
            description="Extract text from a PDF",
            inputSchema={
                "type": "object",
                "required": ["pdf_url"],
                "properties": {
                    "pdf_url": {"type": "string", "description": "PDF URL"},
                    "pages": {"type": "string", "description": "Pages to extract from (default all)"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        async with httpx.AsyncClient(base_url=STIRLING_URL, timeout=60) as client:
            if name == "merge_pdfs":
                # Download PDFs and merge
                files = []
                for i, url in enumerate(arguments["pdf_urls"]):
                    r = await client.get(url)
                    files.append(("files", (f"doc_{i}.pdf", r.content, "application/pdf")))
                r2 = await client.post("/api/v1/merge-pdfs", files=files)
                return [TextContent(type="text", text=json.dumps({
                    "status": r2.status_code,
                    "size_bytes": len(r2.content),
                    "message": f"Merged {len(arguments['pdf_urls'])} PDFs"
                }))]
            
            elif name == "split_pdf":
                pdf_url = arguments["pdf_url"]
                r = await client.get(pdf_url)
                files = {"file": ("doc.pdf", r.content, "application/pdf")}
                data = {"pages": arguments["pages"]} if "pages" in arguments else None
                r2 = await client.post("/api/v1/split-pdf", files=files, data=data)
                return [TextContent(type="text", text=json.dumps({
                    "status": r2.status_code,
                    "message": "PDF split complete"
                }))]
            
            elif name == "pdf_to_images":
                pdf_url = arguments["pdf_url"]
                r = await client.get(pdf_url)
                files = {"file": ("doc.pdf", r.content, "application/pdf")}
                data = {"dpi": str(arguments.get("dpi", 200))}
                r2 = await client.post("/api/v1/pdf-to-images", files=files, data=data)
                return [TextContent(type="text", text=json.dumps({
                    "status": r2.status_code,
                    "message": "PDF converted to images"
                }))]
            
            elif name == "ocr_pdf":
                pdf_url = arguments["pdf_url"]
                r = await client.get(pdf_url)
                files = {"file": ("doc.pdf", r.content, "application/pdf")}
                data = {"language": arguments.get("language", "eng")}
                r2 = await client.post("/api/v1/ocr-pdf", files=files, data=data)
                return [TextContent(type="text", text=json.dumps({
                    "status": r2.status_code,
                    "message": "OCR complete"
                }))]
            
            elif name == "compress_pdf":
                pdf_url = arguments["pdf_url"]
                r = await client.get(pdf_url)
                files = {"file": ("doc.pdf", r.content, "application/pdf")}
                data = {"quality": arguments.get("quality", "medium")}
                r2 = await client.post("/api/v1/compress-pdf", files=files, data=data)
                return [TextContent(type="text", text=json.dumps({
                    "status": r2.status_code,
                    "size_bytes": len(r2.content),
                    "message": "PDF compressed"
                }))]
            
            elif name == "extract_text":
                pdf_url = arguments["pdf_url"]
                r = await client.get(pdf_url)
                files = {"file": ("doc.pdf", r.content, "application/pdf")}
                r2 = await client.post("/api/v1/extract-text", files=files)
                return [TextContent(type="text", text=json.dumps({
                    "text": r2.text[:10000]
                }))]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
