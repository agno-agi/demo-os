"""
Taskboard - Personal Work Planner (Session State + Memory)
==========================================================

A personal work planner that captures your tasks, surfaces what's due, plans
your day, and remembers how you work. It is the memory home for the standalone
agents — the one place where agentic memory is the point, because a planning
assistant should get more personal the more you use it.

Capture → organize → plan → reflect, over a task model people actually track
(priority, effort, due dates, blocked/waiting), with two planning tools:
- ``agenda`` — overdue and due-today triage
- ``plan_my_day`` — ranks open work by priority, due date, and effort

Demonstrates Agno's session state capabilities:
- ``session_state`` — initial state dict persisted across sessions (your tasks)
- ``enable_agentic_state=True`` — agent can update state directly
- ``add_session_state_to_context=True`` — state injected into agent context

…layered with memory:
- ``enable_agentic_memory=True`` — remembers durable preferences and patterns
  (how you categorize, what priority you favor, your routines) across sessions
- ``search_past_sessions=True`` — recalls context from earlier conversations
"""

from agno.agent import Agent

from agents.taskboard.instructions import INSTRUCTIONS
from agents.taskboard.tools import (
    add_task,
    agenda,
    get_summary,
    list_tasks,
    plan_my_day,
    remove_task,
    update_task_status,
)
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
taskboard = Agent(
    id="planner",
    name="Planner",
    description="Personal work planner — captures tasks, plans your day, and remembers how you work.",
    model=MODEL,
    db=agent_db,
    tools=[add_task, update_task_status, remove_task, list_tasks, agenda, plan_my_day, get_summary],
    instructions=INSTRUCTIONS,
    session_state={
        "tasks": [],
        "categories": ["general", "work", "personal"],
    },
    enable_agentic_state=True,
    add_session_state_to_context=True,
    enable_agentic_memory=True,
    search_past_sessions=True,
    num_past_sessions_to_search=5,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
