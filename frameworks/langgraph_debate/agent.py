"""
Debate Bot (LangGraph)
======================

A LangGraph agent that debates any topic. Pro and Con advocates argue in
parallel branches, then a Judge merges both sides and declares a winner.

Demonstrates: LangGraph parallel branches + merge, served through AgentOS.
"""

from agno.agents.langgraph import LangGraphAgent

from app.settings import agent_db
from frameworks.langgraph_debate.graph import build_graph

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
langgraph_debate = LangGraphAgent(
    id="langgraph-debate",
    name="Debate Bot (LangGraph)",
    description="Pro and Con argue in parallel, a Judge declares the winner.",
    db=agent_db,
    graph=build_graph(),
    markdown=True,
)
