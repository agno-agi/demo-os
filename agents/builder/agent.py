"""
Builder - Agent-Building Agent (StudioTool + HITL)
==================================================

"Describe your job and I'll build your assistant."

Builder composes a personalized agent from a conversation, using Agno's StudioTool against the
live AgentOS registry: it interviews the user, discovers the right tools/model from the registry,
creates the assistant behind a confirmation gate, trial-runs it, refines it on feedback, and
publishes it live in this AgentOS.

- StudioTool          — list/create/run/edit/publish agents against the registry. Destructive ops
  (create/edit/delete/publish) are gated by ``requires_confirmation_tools``; ``versions=True`` keeps
  edits as drafts until published.
- Human-in-the-loop   — UserControlFlowTools (free-text) and UserFeedbackTools (multiple-choice) to
  interview the user and collect feedback on trial runs.

Built as a single Agent (not a team): coordinate-mode teams in this Agno build mishandle HITL
pause/resume, orphaning the paused tool call. A single agent resumes cleanly across confirmations.
"""

from agno.agent import Agent
from agno.tools.studio import StudioTool
from agno.tools.user_control_flow import UserControlFlowTools
from agno.tools.user_feedback import UserFeedbackTools

from agents.builder.instructions import INSTRUCTIONS
from app.registry import registry
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
builder = Agent(
    id="builder",
    name="Builder",
    description="Describe your job and Builder composes a personalized assistant — interviewed, built behind approval, trial-run, and published live in the OS.",
    model=MODEL,
    db=agent_db,
    tools=[
        StudioTool(
            registry=registry,
            db=agent_db,
            agents=True,
            versions=True,
            requires_confirmation_tools=[
                "create_agent",
                "edit_agent",
                "delete_agent",
                "publish_component",
            ],
        ),
        UserControlFlowTools(),
        UserFeedbackTools(),
    ],
    instructions=INSTRUCTIONS,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
