"""
Reliability Eval Cases
======================

Expected tool calls per entity. Each case specifies a prompt and the
tool names that MUST be called for the response to be correct.
"""

CASES: list[dict] = [
    # -------------------------------------------------------------------------
    # Helpdesk — HITL tools
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "glass",
        "input": "Restart the auth service, it's down",
        "expected_tools": ["restart_service"],
    },
    {
        "entity_type": "agent",
        "entity_id": "glass",
        "input": "Create a P1 ticket for the payment gateway outage",
        "expected_tools": ["create_support_ticket"],
    },
    {
        "entity_type": "agent",
        "entity_id": "glass",
        "input": "Run diagnostics on the database cluster",
        "expected_tools": ["run_diagnostic"],
    },
    # -------------------------------------------------------------------------
    # Approvals — approval gates
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "ledger",
        "input": "Process a $200 refund for order C-5001",
        "expected_tools": ["process_refund"],
    },
    {
        "entity_type": "agent",
        "entity_id": "ledger",
        "input": "Delete account for user U-1234",
        "expected_tools": ["delete_user_account"],
    },
    {
        "entity_type": "agent",
        "entity_id": "ledger",
        "input": "Export all customer data for compliance review",
        "expected_tools": ["export_customer_data"],
    },
    # -------------------------------------------------------------------------
    # Taskboard — task management
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "pilot",
        "input": "Add a task: Write quarterly report, high priority, work category",
        "expected_tools": ["add_task"],
    },
    {
        "entity_type": "agent",
        "entity_id": "pilot",
        "input": "Show me all my tasks",
        "expected_tools": ["list_tasks"],
    },
    {
        "entity_type": "agent",
        "entity_id": "pilot",
        "input": "What's overdue or due today?",
        "expected_tools": ["agenda"],
    },
    {
        "entity_type": "agent",
        "entity_id": "pilot",
        "input": "Plan my day — what should I focus on?",
        "expected_tools": ["plan_my_day"],
    },
]
