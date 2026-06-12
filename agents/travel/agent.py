"""
Voyager - Travel Booking Concierge (HITL + Guardrails)
======================================================

A travel concierge that books a trip end-to-end, with a human in the loop at
every consequential step. One real task threads all three HITL patterns:
- requires_user_input    (select_flight_details)— traveler supplies flight, seat, and passenger name
- requires_confirmation  (book_flight)          — approve before money is spent
- external_execution     (check_live_fare)       — live fare comes from the airline's pricing service

Plus guardrails:
- OpenAIModerationGuardrail / PIIDetectionGuardrail / PromptInjectionGuardrail (pre-hooks)
- Output guardrail + audit log (post-hooks)
"""

from agno.agent import Agent
from agno.guardrails import OpenAIModerationGuardrail, PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.tools.user_feedback import UserFeedbackTools

from agents.travel.instructions import INSTRUCTIONS
from agents.travel.tools import (
    book_flight,
    charge_payment,
    check_live_fare,
    search_flights,
    select_flight_details,
)
from app.settings import MODEL, agent_db


# ---------------------------------------------------------------------------
# Post-hooks: output guardrail + audit trail
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
        r"\b(?:\d[ -]*?){13,16}\b",  # Card-number-like sequences
    ]
    for pattern in sensitive_patterns:
        if re.search(pattern, content):
            run_output.content = (
                "I'm unable to include that information as it may contain sensitive data. "
                "Card details are handled securely by the payment service and never shown here."
            )
            return


def audit_log(run_output, agent):
    """Post-hook: audit trail for compliance."""
    print(f"[AUDIT] Agent={agent.name} Status={run_output.event}")


# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
travel = Agent(
    id="voyager",
    name="Voyager",
    description="Travel concierge that books trips end-to-end with human-in-the-loop approvals and guardrails.",
    model=MODEL,
    db=agent_db,
    tools=[
        search_flights,
        check_live_fare,
        select_flight_details,
        book_flight,
        charge_payment,
        UserFeedbackTools(),
    ],
    instructions=INSTRUCTIONS,
    pre_hooks=[
        OpenAIModerationGuardrail(),
        PIIDetectionGuardrail(),
        PromptInjectionGuardrail(),
    ],
    post_hooks=[output_guardrail, audit_log],
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
