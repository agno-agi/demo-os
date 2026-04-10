"""
Helpdesk - HITL + Guardrails Demo Agent
========================================

An IT operations helpdesk agent that demonstrates:
- All three HITL patterns (confirmation, user input, external execution)
- PIIDetectionGuardrail as a pre-hook to detect personal information
- PromptInjectionGuardrail as a pre-hook to detect adversarial prompts
- Post-hook audit logging for compliance

Run:
    python -m agents.helpdesk
"""

from agno.agent import Agent
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.tools.user_feedback import UserFeedbackTools

from agents.helpdesk.instructions import INSTRUCTIONS
from agents.helpdesk.tools import create_support_ticket, restart_service, run_diagnostic
from app.settings import MODEL, agent_db


# ---------------------------------------------------------------------------
# Post-hook: audit trail
# ---------------------------------------------------------------------------
def audit_log(run_output, agent):
    """Post-hook: audit trail for compliance."""
    print(f"[AUDIT] Agent={agent.name} Status={run_output.event}")


# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
helpdesk = Agent(
    id="helpdesk",
    name="Helpdesk",
    model=MODEL,
    db=agent_db,
    tools=[restart_service, create_support_ticket, run_diagnostic, UserFeedbackTools()],
    instructions=INSTRUCTIONS,
    pre_hooks=[
        PIIDetectionGuardrail(),
        PromptInjectionGuardrail(),
    ],
    post_hooks=[audit_log],
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
