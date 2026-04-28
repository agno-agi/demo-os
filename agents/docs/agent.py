"""
Docs - Agno Documentation Agent (via LLMs.txt)
===========================

Answers developer questions about the Agno framework by dynamically
fetching documentation pages via the llms.txt protocol. No pre-loading
required -- the agent reads the index and fetches relevant pages on demand.
"""

from agno.agent import Agent

from agents.docs.instructions import INSTRUCTIONS
from agents.docs.tools import get_llms_txt_index, read_llms_txt_url
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
docs_agent = Agent(
    id="docs",
    name="Docs",
    model=MODEL,
    db=agent_db,
    tools=[get_llms_txt_index, read_llms_txt_url],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
