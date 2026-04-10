"""
Analyst Agent
=============

SQL generation, execution, schema introspection, and data quality handling.
The core query engine — writes SQL, fixes errors, learns from mistakes,
and provides insights rather than raw results.
"""

from agno.agent import Agent

from agents.dash.instructions import build_analyst_instructions
from agents.dash.settings import MODEL, agent_db, dash_knowledge, dash_learning
from agents.dash.tools.build import build_analyst_tools

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
analyst = Agent(
    id="analyst",
    name="Analyst",
    role="SQL generation, execution, schema introspection, data quality handling",
    model=MODEL,
    db=agent_db,
    instructions=build_analyst_instructions(),
    knowledge=dash_knowledge,
    search_knowledge=True,
    learning=dash_learning,
    add_learnings_to_context=True,
    tools=build_analyst_tools(dash_knowledge),
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)
