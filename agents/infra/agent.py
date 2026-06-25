"""
Operator - Infrastructure Change Agent (Approvals + Skills + Structured Output)
===============================================================================

An infrastructure change agent that threads three Agno features through one task:
ask it to make an infra change, it drafts a typed, risk-scored plan, then asks you to
approve or reject before it executes — all in a single turn.

- Structured output  — ``draft_plan`` takes and returns a typed, validated ``ChangePlan``
  (Pydantic, nested ``BlastRadius``); the ``risk`` field drives the audit approval path.
- Skills             — ``Skills(loaders=[LocalSkills(...)])`` loads two local SKILL.md
  skills (terraform-changes, incident-runbook) that teach safe change procedure.
- Human-in-the-loop  — ``apply_change`` is gated by a blocking approval
  (``@approval(type="required")``), so the run pauses right after the plan is drafted and a
  pending record appears in the Approvals view, which a human must approve before it executes.

The plan is a tool's typed return value rather than the agent's response schema, so the
confirmation gate can pause the same run that drafts the plan.
"""

from pathlib import Path

from agno.agent import Agent
from agno.skills import LocalSkills, Skills

from agents.infra.instructions import INSTRUCTIONS
from agents.infra.tools import apply_change, draft_plan, inspect_resource
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
SKILLS_PATH = Path(__file__).parent / "skills"

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
infra = Agent(
    id="operator",
    name="Operator",
    description="Infrastructure change agent — drafts a typed, risk-scored plan, gets human approval, then executes.",
    model=MODEL,
    db=agent_db,
    tools=[inspect_resource, draft_plan, apply_change],
    skills=Skills(loaders=[LocalSkills(str(SKILLS_PATH))]),
    instructions=INSTRUCTIONS,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
