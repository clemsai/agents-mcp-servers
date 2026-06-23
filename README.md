# Email MCP Server — AgentMail for AI Agents

**Give AI agents their own email inboxes.** Create, send, receive, and manage email entirely via MCP tools.

## What It Does

This MCP server wraps the [AgentMail](https://agentmail.to) API, giving AI agents:
- **Create inboxes** — Programmatic inbox creation via API
- **Send emails** — Send from any inbox
- **Receive emails** — List, search, and read messages
- **Thread management** — Full conversation context
- **Reply** — Maintain conversation threads

## Quick Start

### 1. Get AgentMail API Key
Sign up at [agentmail.to](https://agentmail.to) (free tier: 3 inboxes, 3K emails/mo)

### 2. Install
```bash
pip install -e /root/agents-mcp-servers
```

### 3. Configure
```bash
export AGENTMAIL_API_KEY="your_key_here"
```

### 4. Add to Claude Desktop / Cursor
```json
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": ["/root/agents-mcp-servers/email_mcp_server.py"],
      "env": {
        "AGENTMAIL_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `create_inbox` | Create a new email inbox |
| `list_inboxes` | List all inboxes |
| `send_email` | Send an email |
| `list_messages` | List messages in inbox |
| `get_message` | Get full message content |
| `reply_to_message` | Reply maintaining thread |
| `search_messages` | Search across messages |
| `get_thread` | Get full conversation thread |

## Publishing

### Smithery
```bash
npx @smithery/cli publish
```

### Official MCP Registry
```bash
npx @modelcontextprotocol/mcp-publisher publish
```

## License
MIT
