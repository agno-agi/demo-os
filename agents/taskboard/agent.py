"""
Taskboard - Session State Demo Agent
=====================================

Demonstrates Agno's session state capabilities:
- ``session_state`` — initial state dict persisted across sessions
- ``enable_agentic_state=True`` — agent can update state directly
- ``add_session_state_to_context=True`` — state injected into agent context
"""

from agno.agent import Agent

from agents.taskboard.instructions import INSTRUCTIONS
from agents.taskboard.tools import add_task, get_summary, list_tasks, remove_task, update_task_status
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
taskboard = Agent(
    id="taskboard",
    name="Taskboard",
    model=MODEL,
    db=agent_db,
    tools=[add_task, update_task_status, list_tasks, remove_task, get_summary],
    instructions=INSTRUCTIONS,
    session_state={
        "tasks": [],
        "categories": ["general", "work", "personal"],
    },
    enable_agentic_state=True,
    add_session_state_to_context=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
