"""HITL smoke tests — validate pause/resume tool behavior.

These tests check that agents pause with the correct tool when HITL
is required. The client parses RunPaused events and includes tool_name
in the response content, so we can use response_contains to verify.
"""

from evals.cases.smoke import SmokeTest

HITL_TESTS: list[SmokeTest] = [
    # -------------------------------------------------------------------------
    # Voyager — 3 HITL patterns in one booking flow
    # -------------------------------------------------------------------------
    SmokeTest(
        id="h.2",
        name="voyager — choices collected via ask_user (MCQ)",
        entity_type="agent",
        entity_id="voyager",
        group="hitl",
        prompt="Help me book a flight from SFO to JFK tomorrow",
        response_matches=[r"(?i)(ask_user|which flight|seat|window|aisle)"],
        response_not_contains=["Traceback"],
        max_duration=40.0,
    ),
    SmokeTest(
        id="h.1",
        name="voyager — booking requires confirmation",
        entity_type="agent",
        entity_id="voyager",
        group="hitl",
        prompt="Book flight FL-4821 for Jordan Lee at USD 420",
        response_contains=["book_flight"],
        max_duration=30.0,
    ),
    SmokeTest(
        id="h.3",
        name="voyager — live fare runs as external execution",
        entity_type="agent",
        entity_id="voyager",
        group="hitl",
        prompt="What's the live fare right now on flight FL-4821?",
        response_contains=["check_live_fare"],
        max_duration=30.0,
    ),
    # -------------------------------------------------------------------------
    # Voyager — search starts the flow (no gate)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="h.4",
        name="voyager — searches flights for a trip",
        entity_type="agent",
        entity_id="voyager",
        group="hitl",
        prompt="Find me flights from San Francisco to New York on 2026-07-15",
        response_matches=[r"(?i)(search_flights|FL-|flight|fare)"],
        response_not_contains=["Traceback"],
        max_duration=30.0,
    ),
    # -------------------------------------------------------------------------
    # Approvals — approval gates
    # -------------------------------------------------------------------------
    SmokeTest(
        id="h.5",
        name="approvals — refund requires approval",
        entity_type="agent",
        entity_id="ledger",
        group="hitl",
        prompt="Process a $50 refund for order C-1042",
        response_contains=["process_refund"],
        max_duration=30.0,
    ),
    SmokeTest(
        id="h.6",
        name="approvals — export requires approval",
        entity_type="agent",
        entity_id="ledger",
        group="hitl",
        prompt="Export all customer data for C-5500",
        response_contains=["export_customer_data"],
        max_duration=30.0,
    ),
]
