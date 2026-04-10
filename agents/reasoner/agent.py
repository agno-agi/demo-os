from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.parallel import ParallelTools
from agno.tools.reasoning import ReasoningTools

from agents.reasoner.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools

reasoner = Agent(
    id="reasoner",
    name="Reasoner",
    model=MODEL,
    db=agent_db,
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=8,
    tools=[ReasoningTools(add_instructions=True), ParallelTools(), *get_exa_mcp_tools()],
    fallback_models=[Claude(id="claude-sonnet-4-5")],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
