"""
Scheduler - Schedule Management Agent
======================================

Creates and manages recurring schedules for agents, teams, and
workflows in AgentOS using SchedulerTools.

Run:
    python -m agents.scheduler
"""

from agno.agent import Agent
from agno.tools.scheduler import SchedulerTools

from agents.scheduler.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
scheduler = Agent(
    id="scheduler",
    name="Scheduler",
    model=MODEL,
    db=agent_db,
    tools=[SchedulerTools(db=agent_db)],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
