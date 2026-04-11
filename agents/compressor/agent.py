"""
Compressor - Tool Result Compression Demo Agent
================================================

Demonstrates Agno's context compression capabilities:
- ``compress_tool_results=True`` — automatically compress tool outputs
- ``CompressionManager`` — custom compression with a smaller/cheaper model
"""

from agno.agent import Agent
from agno.compression import CompressionManager
from agno.models.openai import OpenAIResponses
from agno.tools.duckduckgo import DuckDuckGoTools

from agents.compressor.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
compressor = Agent(
    id="compressor",
    name="Compressor",
    model=MODEL,
    db=agent_db,
    tools=[DuckDuckGoTools(), *get_exa_mcp_tools()],
    instructions=INSTRUCTIONS,
    compress_tool_results=True,
    compression_manager=CompressionManager(
        model=OpenAIResponses(id="gpt-5.4-mini"),
    ),
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
