"""
Reliability Eval Cases
======================

Expected tool calls per entity. Each case specifies a prompt and the
tool names that MUST be called for the response to be correct.
"""

CASES: list[dict] = [
    # -------------------------------------------------------------------------
    # Voyager — HITL tools
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "voyager",
        "input": "Find flights from Chicago to Miami on 2026-09-10",
        "expected_tools": ["search_flights"],
    },
    {
        "entity_type": "agent",
        "entity_id": "voyager",
        "input": "Book flight FL-4821 for Jordan Lee at USD 420",
        "expected_tools": ["book_flight"],
    },
    {
        "entity_type": "agent",
        "entity_id": "voyager",
        "input": "Email the confirmed itinerary for booking BK-04821 to jordan@example.com",
        "expected_tools": ["send_email"],
    },
    # -------------------------------------------------------------------------
    # Operator — plan-then-apply approval gates
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "operator",
        "input": "Scale web-cluster from 4 to 8 replicas in production",
        "expected_tools": ["draft_plan"],
    },
    {
        "entity_type": "agent",
        "entity_id": "operator",
        "input": "Destroy the orders-db Postgres instance",
        "expected_tools": ["draft_plan"],
    },
    {
        "entity_type": "agent",
        "entity_id": "operator",
        "input": "Rotate the payments-api-key credential in production",
        "expected_tools": ["draft_plan"],
    },
    # -------------------------------------------------------------------------
    # Taskboard — task management
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "planner",
        "input": "Add a task: Write quarterly report, high priority, work category",
        "expected_tools": ["add_task"],
    },
    {
        "entity_type": "agent",
        "entity_id": "planner",
        "input": "Show me all my tasks",
        "expected_tools": ["list_tasks"],
    },
    {
        "entity_type": "agent",
        "entity_id": "planner",
        "input": "What's overdue or due today?",
        "expected_tools": ["agenda"],
    },
    {
        "entity_type": "agent",
        "entity_id": "planner",
        "input": "Plan my day — what should I focus on?",
        "expected_tools": ["plan_my_day"],
    },
]
