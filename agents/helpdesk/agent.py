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
from agno.guardrails import OpenAIModerationGuardrail, PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.tools.user_feedback import UserFeedbackTools

from agents.helpdesk.instructions import INSTRUCTIONS
from agents.helpdesk.tools import create_support_ticket, restart_service, run_diagnostic
from app.settings import MODEL, agent_db


# ---------------------------------------------------------------------------
# Post-hook: audit trail
# ---------------------------------------------------------------------------
def output_guardrail(run_output, agent):
    """Post-hook: block responses that accidentally leak sensitive data patterns."""
    import re

    content = run_output.content or ""
    sensitive_patterns = [
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI API keys
        r"postgres://[^\s]+",  # Connection strings
        r"OPENAI_API_KEY\s*=",  # Env var assignments
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN patterns
    ]
    for pattern in sensitive_patterns:
        if re.search(pattern, content):
            run_output.content = (
                "I'm unable to provide that information as it may contain sensitive data. "
                "Please contact your system administrator directly."
            )
            return


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
        OpenAIModerationGuardrail(),
        PIIDetectionGuardrail(),
        PromptInjectionGuardrail(),
    ],
    post_hooks=[output_guardrail, audit_log],
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
