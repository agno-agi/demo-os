"""Support Triage - Router + Condition workflow.

Demonstrates:
- ``Router`` — routes to specialist agents based on classifier output
- ``Condition`` — conditionally escalates high-severity issues
- ``StepInput`` — passing data between workflow steps
"""

from agno.agent import Agent
from agno.workflow import Condition, Router, Step, Workflow
from agno.workflow.types import StepInput

from app.settings import MODEL, agent_db
from workflows.support_triage.instructions import (
    ACCOUNT_INSTRUCTIONS,
    BILLING_INSTRUCTIONS,
    CLASSIFIER_INSTRUCTIONS,
    ESCALATION_INSTRUCTIONS,
    TECHNICAL_INSTRUCTIONS,
)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

classifier = Agent(
    id="support-triage-classifier",
    name="Classifier",
    model=MODEL,
    db=agent_db,
    instructions=CLASSIFIER_INSTRUCTIONS,
)

billing_specialist = Agent(
    id="support-triage-billing",
    name="Billing Specialist",
    model=MODEL,
    db=agent_db,
    instructions=BILLING_INSTRUCTIONS,
    markdown=True,
)

technical_specialist = Agent(
    id="support-triage-technical",
    name="Technical Specialist",
    model=MODEL,
    db=agent_db,
    instructions=TECHNICAL_INSTRUCTIONS,
    markdown=True,
)

account_specialist = Agent(
    id="support-triage-account",
    name="Account Specialist",
    model=MODEL,
    db=agent_db,
    instructions=ACCOUNT_INSTRUCTIONS,
    markdown=True,
)

escalation_agent = Agent(
    id="support-triage-escalation",
    name="Escalation Handler",
    model=MODEL,
    db=agent_db,
    instructions=ESCALATION_INSTRUCTIONS,
    markdown=True,
)


# ---------------------------------------------------------------------------
# Router selector — parse classifier output to pick a specialist
# ---------------------------------------------------------------------------
def route_to_specialist(step_input: StepInput) -> list[Step]:
    """Route to the correct specialist based on the classifier's CATEGORY line."""
    content = str(step_input.previous_step_content or "").upper()
    if "CATEGORY: BILLING" in content:
        return [billing_step]
    if "CATEGORY: ACCOUNT" in content:
        return [account_step]
    # Default to technical for unrecognized categories
    return [technical_step]


# ---------------------------------------------------------------------------
# Condition evaluator — escalate high/critical severity
# ---------------------------------------------------------------------------
def is_high_severity(step_input: StepInput) -> bool:
    """Check if the classified severity warrants escalation."""
    # Look through all previous step outputs for the classifier's content
    for output in (step_input.previous_step_outputs or {}).values():
        content = str(output.content or "").upper()
        if "SEVERITY: HIGH" in content or "SEVERITY: CRITICAL" in content:
            return True
    return False


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

billing_step = Step(name="Billing", agent=billing_specialist)
technical_step = Step(name="Technical", agent=technical_specialist)
account_step = Step(name="Account", agent=account_specialist)

# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

support_triage = Workflow(
    id="support-triage",
    name="Support Triage",
    steps=[
        Step(name="Classify", agent=classifier),
        Router(
            name="Route to Specialist",
            selector=route_to_specialist,  # type: ignore[arg-type]
            choices=[billing_step, technical_step, account_step],
        ),
        Condition(
            name="Escalation Check",
            evaluator=is_high_severity,
            steps=[Step(name="Escalate", agent=escalation_agent)],
        ),
    ],
)
