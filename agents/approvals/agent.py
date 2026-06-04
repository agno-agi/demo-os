"""
Approvals - Approval Flows Demo Agent
======================================

A compliance and finance agent demonstrating Agno's approval patterns:
- @approval decorator: blocking approval before execution
- @approval(type="audit"): audit trail logging
- requires_confirmation=True: HITL confirmation
"""

from agno.agent import Agent

from agents.approvals.instructions import INSTRUCTIONS
from agents.approvals.tools import delete_user_account, export_customer_data, generate_report, process_refund
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
approvals = Agent(
    id="approvals",
    name="Approvals",
    model=MODEL,
    db=agent_db,
    tools=[process_refund, delete_user_account, export_customer_data, generate_report],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
