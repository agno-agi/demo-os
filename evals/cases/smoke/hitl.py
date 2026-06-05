"""HITL smoke tests — validate pause/resume tool behavior.

These tests check that agents pause with the correct tool when HITL
is required. The client parses RunPaused events and includes tool_name
in the response content, so we can use response_contains to verify.
"""

from evals.cases.smoke import SmokeTest

HITL_TESTS: list[SmokeTest] = [
    # -------------------------------------------------------------------------
    # Helpdesk — 3 HITL patterns
    # -------------------------------------------------------------------------
    SmokeTest(
        id="h.1",
        name="helpdesk — restart requires confirmation",
        entity_type="agent",
        entity_id="helpdesk",
        group="hitl",
        prompt="Restart the auth service",
        response_contains=["restart_service"],
        max_duration=30.0,
    ),
    SmokeTest(
        id="h.2",
        name="helpdesk — ticket requires user input",
        entity_type="agent",
        entity_id="helpdesk",
        group="hitl",
        prompt="Create a support ticket for slow API responses",
        response_contains=["create_support_ticket"],
        max_duration=30.0,
    ),
    SmokeTest(
        id="h.3",
        name="helpdesk — diagnostic external execution",
        entity_type="agent",
        entity_id="helpdesk",
        group="hitl",
        prompt="Run diagnostics on the database cluster",
        response_contains=["run_diagnostic"],
        max_duration=30.0,
    ),
    # -------------------------------------------------------------------------
    # Helpdesk — ask_user (structured question)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="h.4",
        name="helpdesk — asks structured question",
        entity_type="agent",
        entity_id="helpdesk",
        group="hitl",
        prompt="Something's wrong with one of our services but I'm not sure which — help me triage it.",
        response_contains=["ask_user"],
        max_duration=30.0,
    ),
    # -------------------------------------------------------------------------
    # Approvals — approval gates
    # -------------------------------------------------------------------------
    SmokeTest(
        id="h.5",
        name="approvals — refund requires approval",
        entity_type="agent",
        entity_id="approvals",
        group="hitl",
        prompt="Process a $50 refund for order C-1042",
        response_contains=["process_refund"],
        max_duration=30.0,
    ),
    SmokeTest(
        id="h.6",
        name="approvals — export requires approval",
        entity_type="agent",
        entity_id="approvals",
        group="hitl",
        prompt="Export all customer data for C-5500",
        response_contains=["export_customer_data"],
        max_duration=30.0,
    ),
]
