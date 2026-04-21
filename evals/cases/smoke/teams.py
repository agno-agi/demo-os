"""Smoke test cases for the 11 teams."""

from evals.cases.smoke import SmokeTest

TEAM_TESTS: list[SmokeTest] = [
    # -------------------------------------------------------------------------
    # Pal (personal knowledge team)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.1",
        name="pal — capabilities",
        entity_type="team",
        entity_id="pal",
        group="teams",
        prompt="What can you do?",
        response_matches=[r"(?i)(help|research|knowledge|wiki)"],
        response_not_contains=["Traceback"],
        max_duration=60.0,
    ),
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
    # -------------------------------------------------------------------------
    # Research — coordinate mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.4",
        name="research-coordinate — AI agent market",
        entity_type="team",
        entity_id="research-coordinate",
        group="teams",
        prompt="Research the AI agent framework market",
        response_matches=[r"(?i)(agent|framework|market)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=90.0,
    ),
    # -------------------------------------------------------------------------
    # Research — route mode (should route to single specialist)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.5",
        name="research-route — market size",
        entity_type="team",
        entity_id="research-route",
        group="teams",
        prompt="What is the market cap of the AI agent industry?",
        response_matches=[r"(?i)(billion|million|\$|market.*(size|cap)|agent)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=60.0,
    ),
    # -------------------------------------------------------------------------
    # Research — broadcast mode (all agents, multiple perspectives)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.6",
        name="research-broadcast — AI developments",
        entity_type="team",
        entity_id="research-broadcast",
        group="teams",
        prompt="Assess the future of AI agents",
        response_matches=[r"(?i)(ai|agent|development|future)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=90.0,
    ),
    # -------------------------------------------------------------------------
    # Research — tasks mode (decomposes into subtasks)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.7",
        name="research-tasks — compare frameworks",
        entity_type="team",
        entity_id="research-tasks",
        group="teams",
        prompt="Compare the top 3 AI agent frameworks",
        response_matches=[r"(?i)(agent|framework|compar)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=90.0,
    ),
    # -------------------------------------------------------------------------
    # Investment — coordinate mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.8",
        name="investment-coordinate — NVIDIA",
        entity_type="team",
        entity_id="investment-coordinate",
        group="teams",
        prompt="Should we invest in NVIDIA?",
        response_matches=[r"(?i)(nvidia|nvda|invest|recommend|analy)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=90.0,
    ),
    # -------------------------------------------------------------------------
    # Investment — route mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.9",
        name="investment-route — AAPL P/E",
        entity_type="team",
        entity_id="investment-route",
        group="teams",
        prompt="What's AAPL's P/E ratio?",
        response_matches=[r"(?i)(apple|aapl|p.e|ratio|earnings)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=60.0,
    ),
    # -------------------------------------------------------------------------
    # Investment — broadcast mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.10",
        name="investment-broadcast — assess NVDA",
        entity_type="team",
        entity_id="investment-broadcast",
        group="teams",
        prompt="All analysts: assess NVDA",
        response_matches=[r"(?i)(nvda|nvidia|analy|risk|technical|fundamental)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=90.0,
    ),
    # -------------------------------------------------------------------------
    # Investment — tasks mode
    # -------------------------------------------------------------------------
    SmokeTest(
        id="t.11",
        name="investment-tasks — tech portfolio",
        entity_type="team",
        entity_id="investment-tasks",
        group="teams",
        prompt="Build a diversified tech portfolio",
        response_matches=[r"(?i)(portfolio|diversif|stock|allocation)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=90.0,
    ),
]
