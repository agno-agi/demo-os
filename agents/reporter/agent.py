from agno.agent import Agent
from agno.tools.calculator import CalculatorTools
from agno.tools.file_generation import FileGenerationTools

from agents.reporter.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools

reporter = Agent(
    id="reporter",
    name="Reporter",
    model=MODEL,
    db=agent_db,
    tools=[FileGenerationTools(), CalculatorTools(), *get_exa_mcp_tools()],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
