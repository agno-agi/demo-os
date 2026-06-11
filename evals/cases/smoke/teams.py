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
    # Investment — coordinate mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.8",
        name="investment-coordinate — recommendation includes risk and dollar allocation",
        entity_type="team",
        entity_id="quorum",
        group="teams",
        prompt="Evaluate NVIDIA for inclusion in the fund and propose a position size.",
        response_matches=[
            r"(?i)(nvidia|nvda)",
            r"(?i)(buy|hold|pass)",
            r"\$[\d,.]+\s*(M|million|K|thousand)?",
            r"(?i)(risk|drawdown|beta|volatility|position\s+limit)",
        ],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=240.0,
    ),
    # -------------------------------------------------------------------------
    # Investment — route mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.9",
        name="investment-route — AAPL P/E",
        entity_type="team",
        entity_id="switch",
        group="teams",
        prompt="What's AAPL's P/E ratio?",
        response_matches=[r"(?i)(apple|aapl|p.e|ratio|earnings)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=60.0,
    ),
    SmokeTest(
        id="t.9.2",
        name="investment-route — chart/momentum question reaches Technical Analyst",
        entity_type="team",
        entity_id="switch",
        group="teams",
        prompt="What does TSLA's 50-day vs 200-day moving average look like right now?",
        response_matches=[r"(?i)(tsla|tesla|moving\s+average|50.day|200.day|sma|trend)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=90.0,
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
    # -------------------------------------------------------------------------
    # Investment — tasks mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.11",
        name="investment-tasks — tech portfolio",
        entity_type="team",
        entity_id="foreman",
        group="teams",
        prompt="Build a diversified tech portfolio",
        response_matches=[r"(?i)(portfolio|diversif|stock|allocation)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=250.0,
    ),
]
