"""
Docs - Agno Documentation Agent (via LLMs.txt)
===========================

Answers developer questions about the Agno framework by dynamically
fetching documentation pages via the llms.txt protocol. No pre-loading
required -- the agent reads the index and fetches relevant pages on demand.
"""

from agno.agent import Agent
from agno.tools.llms_txt import LLMsTxtTools

from agents.docs.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
docs_agent = Agent(
    id="docs",
    name="Docs",
    model=MODEL,
    db=agent_db,
    tools=[LLMsTxtTools(allowed_hosts=["docs.agno.com"])],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
