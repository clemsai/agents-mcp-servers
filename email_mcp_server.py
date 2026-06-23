"""
Email MCP Server — AgentMail wrapper for AI agents.
Gives AI agents full email inbox capabilities via AgentMail API.

Tools:
- send_email: Send an email from an inbox
- list_inboxes: List all inboxes  
- list_messages: List messages in an inbox
- get_message: Get a specific message with full content
- reply_to_message: Reply to a message in thread

Usage:
    AGENTMAIL_API_KEY=am_us_... python email_mcp_server.py
    
    Or install as MCP server in Claude Desktop / Cursor:
    {
      "mcpServers": {
        "email": {
          "command": "python",
          "args": ["/root/agents-mcp-servers/email_mcp_server.py"],
          "env": {"AGENTMAIL_API_KEY": "am_us_..."}
        }
      }
    }
"""
import os
import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize AgentMail client
from agentmail import AgentMail

api_key = os.environ.get("AGENTMAIL_API_KEY", "")
client = AgentClient(api_key) if api_key else None

server = Server("email-agentmail")


class AgentClient:
    """Thin wrapper around AgentMail SDK for MCP exposure."""
    
    def __init__(self, api_key: str):
        self._client = AgentMail(api_key=api_key)
    
    def list_inboxes(self):
        result = self._client.inboxes.list()
        return [{"inbox_id": i.inbox_id, "email": i.email, "display_name": i.display_name} for i in result.inboxes]
    
    def send_email(self, inbox_id: str, to: str, subject: str, text: str, html: str = None):
        kwargs = {"inbox_id": inbox_id, "to": to, "subject": subject, "text": text}
        if html:
            kwargs["html"] = html
        msg = self._client.inboxes.messages.send(**kwargs)
        return {"message_id": str(msg.message_id), "thread_id": str(msg.thread_id)}
    
    def list_messages(self, inbox_id: str, limit: int = 25):
        result = self._client.inboxes.messages.list(inbox_id=inbox_id, limit=limit)
        return [{"id": m.id, "subject": m.subject, "from": m.from_address, "extracted_text": m.extracted_text} for m in result.messages]
    
    def get_message(self, inbox_id: str, message_id: str):
        msg = self._client.inboxes.messages.get(inbox_id=inbox_id, message_id=message_id)
        return {"id": msg.id, "subject": msg.subject, "from": msg.from_address, "to": msg.to, "extracted_text": msg.extracted_text, "text": msg.text}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="send_email",
            description="Send an email from an agent's inbox. Returns message_id and thread_id.",
            inputSchema={
                "type": "object",
                "required": ["inbox_id", "to", "subject", "text"],
                "properties": {
                    "inbox_id": {"type": "string", "description": "Sender inbox ID/address (e.g. clemproject@agentmail.to)"},
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "text": {"type": "string", "description": "Email body text"},
                    "html": {"type": "string", "description": "Optional HTML body"}
                }
            }
        ),
        Tool(
            name="list_inboxes",
            description="List all email inboxes in the AgentMail account",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="list_messages",
            description="List messages in an inbox",
            inputSchema={
                "type": "object",
                "required": ["inbox_id"],
                "properties": {
                    "inbox_id": {"type": "string", "description": "Inbox ID/address"},
                    "limit": {"type": "integer", "description": "Max messages (default 25)"}
                }
            }
        ),
        Tool(
            name="get_message",
            description="Get a specific email message with full content",
            inputSchema={
                "type": "object",
                "required": ["inbox_id", "message_id"],
                "properties": {
                    "inbox_id": {"type": "string", "description": "Inbox ID/address"},
                    "message_id": {"type": "string", "description": "Message ID"}
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if not client:
        return [TextContent(type="text", text="ERROR: AGENTMAIL_API_KEY not set")]
    
    try:
        if name == "send_email":
            result = client.send_email(**arguments)
        elif name == "list_inboxes":
            result = client.list_inboxes()
        elif name == "list_messages":
            result = client.list_messages(**arguments)
        elif name == "get_message":
            result = client.get_message(**arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
