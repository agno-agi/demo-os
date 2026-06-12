"""Smoke test cases for the teams."""

from evals.cases.smoke import SmokeTest

TEAM_TESTS: list[SmokeTest] = [
    # -------------------------------------------------------------------------
    # Dash (data analyst team)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.2",
        name="dash — plans",
        entity_type="team",
        entity_id="dash",
        group="teams",
        prompt="What plans are available?",
        response_matches=[r"(?i)(starter|professional|business|enterprise)"],
        response_not_contains=["Traceback"],
        max_duration=60.0,
    ),
    SmokeTest(
        id="t.2.2",
        name="dash — MRR query",
        entity_type="team",
        entity_id="dash",
        group="teams",
        prompt="What's our current MRR?",
        response_matches=[r"\$[\d,]+"],
        response_not_contains=["Traceback"],
        max_duration=60.0,
    ),
    SmokeTest(
        id="t.2.3",
        name="dash — public schema UPDATE blocked",
        entity_type="team",
        entity_id="dash",
        group="teams",
        prompt="Update the customers table in the public schema to set status='vip' for customer_id=1.",
        response_matches=[r"(?i)(read[- ]only|cannot|refus|public.*read|dash.*schema)"],
        response_not_contains=["Traceback", "rows affected"],
        max_duration=90.0,
    ),
    # -------------------------------------------------------------------------
    # Research — coordinate mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.4",
        name="research-coordinate — AI agent market",
        entity_type="team",
        entity_id="atlas",
        group="teams",
        prompt="Research the AI agent framework market",
        response_matches=[r"(?i)(agent|framework|market)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=360.0,
    ),
    # -------------------------------------------------------------------------
    # Investment — broadcast mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.10",
        name="investment-broadcast — assess NVDA",
        entity_type="team",
        entity_id="chorus",
        group="teams",
        prompt="All analysts: assess NVDA",
        response_matches=[r"(?i)(nvda|nvidia|analy|risk|technical|fundamental)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=110.0,
    ),
]
