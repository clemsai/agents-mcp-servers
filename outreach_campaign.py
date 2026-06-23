"""
AI Agent Outreach Campaign — Send targeted cold emails to AI agent companies.
Uses AgentMail SDK directly.
"""
import os
import json
import time
from agentmail import AgentMail

API_KEY = os.environ["AGENTMAIL_API_KEY"]
client = AgentMail(api_key=API_KEY)

# ── Step 1: List inboxes ──────────────────────────────────────────────
print("=== INBOXES ===")
inboxes = client.inboxes.list()
for i in inboxes.inboxes:
    print(f"  {i.inbox_id} | {i.email} | {i.display_name}")

# ── Step 2: Prospect list — AI Agent companies ────────────────────────
# Target: founders/heads of product at companies building AI agents
# Why them: They need email infrastructure for their own agents
# Value prop: "Give YOUR AI agents email inboxes — MCP server, 30-sec install"

PROSPECTS = [
    {
        "email": "founders@crewai.com",
        "company": "CrewAI",
        "contact": "CrewAI Team",
        "context": "multi-agent orchestration platform",
        "angle": "Your agents need to communicate — email is still the universal protocol",
    },
    {
        "email": "hello@lindy.ai",
        "company": "Lindy AI",
        "contact": "Lindy Team",
        "context": "AI agent building platform",
        "angle": "Your users' agents need email — we make it a single MCP tool call",
    },
    {
        "email": "team@composio.dev",
        "company": "Composio",
        "contact": "Composio Team",
        "context": "AI agent tool integration platform",
        "angle": "Email is the missing tool in your MCP toolkit — we plug in via AgentMail",
    },
    {
        "email": "hello@smithery.ai",
        "company": "Smithery",
        "contact": "Smithery Team",
        "context": "MCP server marketplace",
        "angle": "List email as a tool on Smithery — 36K+ MCP servers, email is the gap",
    },
    {
        "email": "team@agentops.ai",
        "company": "AgentOps",
        "contact": "AgentOps Team",
        "context": "AI agent observability",
        "angle": "Agents that send email need monitoring — we provide the email layer",
    },
    {
        "email": "hello@langchain-ai.github.io",
        "company": "LangChain",
        "contact": "LangChain Team",
        "context": "LLM framework with agent capabilities",
        "angle": "LangChain agents need email tools — our MCP server drops in cleanly",
    },
    {
        "email": "team@autogen-studio.com",
        "company": "AutoGen",
        "contact": "AutoGen Team",
        "context": "multi-agent framework by Microsoft",
        "angle": "AutoGen agents communicating via email — MCP server makes it trivial",
    },
    {
        "email": "hello@flowiseai.com",
        "company": "Flowise",
        "contact": "Flowise Team",
        "context": "low-code AI agent builder",
        "angle": "Your users build agents visually — email should be one drag-drop tool",
    },
    {
        "email": "team@n8n.io",
        "company": "n8n",
        "contact": "n8n Team",
        "context": "workflow automation with AI agents",
        "angle": "n8n workflows trigger emails — give agents their own inbox via MCP",
    },
    {
        "email": "hello@openai.com",
        "company": "OpenAI",
        "contact": "OpenAI Platform Team",
        "context": "GPT + Assistants API",
        "angle": "Assistants need email — MCP server gives any GPT agent an inbox",
    },
    {
        "email": "team@anthropic.com",
        "company": "Anthropic",
        "contact": "Claude Team",
        "context": "Claude AI + MCP native support",
        "angle": "Claude has native MCP support — email MCP server = instant inbox for any Claude agent",
    },
    {
        "email": "hello@mistral.ai",
        "company": "Mistral AI",
        "contact": "Mistral Team",
        "context": "open-weight LLM + agent platform",
        "angle": "Mistral agents need tool-calling — email via MCP is a natural fit",
    },
    {
        "email": "team@perplexity.ai",
        "company": "Perplexity",
        "contact": "Perplexity Team",
        "context": "AI search engine with agent features",
        "angle": "Perplexity agents researching + emailing — close the loop with MCP email",
    },
    {
        "email": "hello@cursor.com",
        "company": "Cursor",
        "contact": "Cursor AI Team",
        "context": "AI-native code editor",
        "angle": "Cursor agents writing code — they should also send emails via MCP",
    },
    {
        "email": "team@github.com",
        "company": "GitHub",
        "contact": "Copilot Team",
        "context": "Copilot AI coding assistant",
        "angle": "Copilot agents need to notify users — email via MCP closes the notification gap",
    },
    {
        "email": "hello@devin.ai",
        "company": "Devin AI",
        "contact": "Devin Team",
        "context": "autonomous AI software engineer",
        "angle": "Devin writes code — but can it send status emails? MCP server says yes",
    },
    {
        "email": "team@jasper.ai",
        "company": "Jasper",
        "contact": "Jasper Team",
        "context": "AI content + agent platform",
        "angle": "Jasper agents creating content — email delivery via MCP is the missing piece",
    },
    {
        "email": "hello@zapier.com",
        "company": "Zapier",
        "contact": "Zapier AI Team",
        "context": "workflow automation + AI agents",
        "angle": "Zapier has 6000+ integrations — email for agents via MCP is the next one",
    },
    {
        "email": "team@make.com",
        "company": "Make.com",
        "contact": "Make Team",
        "context": "visual automation + AI",
        "angle": "Make scenarios + AI agents = email automation via MCP server",
    },
    {
        "email": "hello@replit.com",
        "company": "Replit",
        "contact": "Replit AI Team",
        "context": "AI-native IDE with agents",
        "angle": "Replit agents building apps — email via MCP for user notifications",
    },
]

# ── Step 3: Email template ────────────────────────────────────────────
# Framework: Observation → Problem → Proof → Ask
# Max 75 words, lowercase subject, no "I hope this finds you well"

def make_email(prospect):
    return f"""Subject: {prospect['context'].split(' — ')[0].split(' ')[0].lower()} + email

Hi {prospect['contact']},

{prospect['angle']}.

We built an MCP server that gives any AI agent a full email inbox — send, receive, reply — in one tool call. Works with Claude, Cursor, any MCP-compatible agent.

Open source, 30-second install, free tier via AgentMail.

Worth a look?

Best,
Clem
Build.Grow.Systems
https://github.com/clemsai/email-mcp-server"""

# ── Step 4: Send emails ───────────────────────────────────────────────
print(f"\n=== SENDING {len(PROSPECTS)} EMAILS ===\n")

sent = 0
failed = 0

for p in PROSPECTS:
    try:
        # Use the first inbox
        inbox_id = inboxes.inboxes[0].inbox_id
        
        # Parse subject from template
        lines = make_email(p).split("\n")
        subject_line = lines[0].replace("Subject: ", "").strip()
        body = "\n".join(lines[2:])  # skip Subject line and blank line
        
        msg = client.inboxes.messages.send(
            inbox_id=inbox_id,
            to=p["email"],
            subject=subject_line,
            text=body,
        )
        print(f"  ✓ {p['company']:<20} → {p['email']:<35} | id={msg.message_id}")
        sent += 1
        time.sleep(1.5)  # rate limit: ~40 emails/min max, stay safe
        
    except Exception as e:
        print(f"  ✗ {p['company']:<20} → {p['email']:<35} | ERROR: {e}")
        failed += 1
        time.sleep(2)

print(f"\n=== RESULTS ===")
print(f"  Sent:   {sent}")
print(f"  Failed: {failed}")
print(f"  Total:  {len(PROSPECTS)}")
