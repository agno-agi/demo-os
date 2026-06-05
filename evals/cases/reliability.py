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
        "entity_id": "helpdesk",
        "input": "Restart the auth service, it's down",
        "expected_tools": ["restart_service"],
    },
    {
        "entity_type": "agent",
        "entity_id": "helpdesk",
        "input": "Create a P1 ticket for the payment gateway outage",
        "expected_tools": ["create_support_ticket"],
    },
    {
        "entity_type": "agent",
        "entity_id": "helpdesk",
        "input": "Run diagnostics on the database cluster",
        "expected_tools": ["run_diagnostic"],
    },
    # -------------------------------------------------------------------------
    # Approvals — approval gates
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "approvals",
        "input": "Process a $200 refund for order C-5001",
        "expected_tools": ["process_refund"],
    },
    {
        "entity_type": "agent",
        "entity_id": "approvals",
        "input": "Delete account for user U-1234",
        "expected_tools": ["delete_user_account"],
    },
    {
        "entity_type": "agent",
        "entity_id": "approvals",
        "input": "Export all customer data for compliance review",
        "expected_tools": ["export_customer_data"],
    },
    # -------------------------------------------------------------------------
    # Taskboard — task management
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "taskboard",
        "input": "Add a task: Write quarterly report, high priority, work category",
        "expected_tools": ["add_task"],
    },
    {
        "entity_type": "agent",
        "entity_id": "taskboard",
        "input": "Show me all my tasks",
        "expected_tools": ["list_tasks"],
    },
]
