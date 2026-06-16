"""
MCP - Agno Documentation Agent (via MCP)
==========================================

Queries docs.agno.com directly through MCP, so answers always reflect
the latest documentation. No local knowledge base needed.
"""

from agno.agent import Agent
from agno.tools.mcp import MCPTools

from agents.mcp.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
mcp_agent = Agent(
    id="docs",
    name="Docs",
    description="Answers questions about Agno using live documentation via MCP tools.",
    model=MODEL,
    db=agent_db,
    tools=[MCPTools(url="https://docs.agno.com/mcp")],
    instructions=INSTRUCTIONS,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
