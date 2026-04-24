"""Smoke test cases for the 5 workflows."""

from evals.cases.smoke import SmokeTest

WORKFLOW_TESTS: list[SmokeTest] = [
    # -------------------------------------------------------------------------
    # Morning Brief (parallel gather -> synthesize)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.1",
        name="morning-brief — daily briefing",
        entity_type="workflow",
        entity_id="morning-brief",
        group="workflows",
        prompt="Generate my morning briefing",
        response_matches=[r"(?i)(brief|news|summary|today)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    # -------------------------------------------------------------------------
    # AI Research (4 parallel researchers -> synthesize)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.2",
        name="ai-research — AI today",
        entity_type="workflow",
        entity_id="ai-research",
        group="workflows",
        prompt="What's happening in AI today?",
        response_matches=[r"(?i)(ai|research|model|development)"],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=270.0,
    ),
    # -------------------------------------------------------------------------
    # Content Pipeline (parallel + loop + condition)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.3",
        name="content-pipeline — AI agents post",
        entity_type="workflow",
        entity_id="content-pipeline",
        group="workflows",
        prompt="Write a short post about AI agents",
        response_matches=[r"(?i)(agent|content|ai)"],
        response_not_contains=["Traceback"],
        timeout=180.0,
        max_duration=180.0,
    ),
    # -------------------------------------------------------------------------
    # Repo Walkthrough (code -> script -> narrated audio)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.4",
        name="repo-walkthrough — Dash codebase",
        entity_type="workflow",
        entity_id="repo-walkthrough",
        group="workflows",
        prompt="Walk me through the Dash codebase",
        response_matches=[r"(?i)(dash|code|agent|team|analyst)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    # -------------------------------------------------------------------------
    # Support Triage (classify -> route -> escalate)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.5",
        name="support-triage — billing issue",
        entity_type="workflow",
        entity_id="support-triage",
        group="workflows",
        prompt="I was charged twice for my subscription this month",
        response_matches=[r"(?i)(billing|charge|refund|subscription|resolv)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    SmokeTest(
        id="w.5.2",
        name="support-triage — technical issue",
        entity_type="workflow",
        entity_id="support-triage",
        group="workflows",
        prompt="The API is returning 500 errors on every request since this morning",
        response_matches=[r"(?i)(error|technical|api|investigat|diagnos)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
]
