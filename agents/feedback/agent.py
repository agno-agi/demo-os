"""
Feedback - User Feedback Demo Agent
======================================

A planning concierge that demonstrates structured user feedback collection
and control flow interrupts via Agno's UserFeedbackTools and
UserControlFlowTools. The agent uses `ask_user` for structured questions
with predefined options and control flow tools for branching based on
user choices.

Run:
    python -m agents.feedback
"""

from agno.agent import Agent
from agno.tools.user_control_flow import UserControlFlowTools
from agno.tools.user_feedback import UserFeedbackTools

from agents.feedback.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
feedback = Agent(
    id="feedback",
    name="Feedback",
    model=MODEL,
    db=agent_db,
    tools=[UserFeedbackTools(), UserControlFlowTools()],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
