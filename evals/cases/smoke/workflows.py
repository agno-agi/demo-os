"""Smoke test cases for the 5 workflows."""

from evals.cases.smoke import SmokeTest

WORKFLOW_TESTS: list[SmokeTest] = [
    # -------------------------------------------------------------------------
    # Morning Brief (parallel gather -> synthesize)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.1",
        name="morning-brief — five-section daily briefing",
        entity_type="workflow",
        entity_id="dawn",
        group="workflows",
        prompt="Generate my morning briefing",
        response_matches=[
            r"(?i)##\s*Today at a Glance",
            r"(?i)##\s*Priority Actions",
            r"(?i)##\s*Schedule",
            r"(?i)##\s*Inbox Highlights",
            r"(?i)##\s*Industry Pulse",
        ],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=180.0,
    ),
    # -------------------------------------------------------------------------
    # AI Research (4 parallel researchers -> synthesize)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.2",
        name="ai-research — five-section AI brief",
        entity_type="workflow",
        entity_id="pulse",
        group="workflows",
        prompt="What's happening in AI today?",
        response_matches=[
            r"(?i)##\s*Top Stories",
            r"(?i)##\s*Models\s*&?\s*Releases",
            r"(?i)##\s*Products\s*&?\s*Startups",
            r"(?i)##\s*Infrastructure\s*&?\s*Tools",
            r"(?i)##\s*Policy\s*&?\s*Industry",
        ],
        response_not_contains=["Traceback"],
        requires=["EXA_API_KEY"],
        max_duration=300.0,
    ),
    # -------------------------------------------------------------------------
    # Content Pipeline (parallel + loop + condition)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.3",
        name="content-pipeline — AI agents post",
        entity_type="workflow",
        entity_id="press",
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
        entity_id="echo",
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
        entity_id="beacon",
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
        entity_id="beacon",
        group="workflows",
        prompt="The API is returning 500 errors on every request since this morning",
        response_matches=[r"(?i)(error|technical|api|investigat|diagnos)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    SmokeTest(
        id="w.5.3",
        name="support-triage — low severity does not escalate",
        entity_type="workflow",
        entity_id="beacon",
        group="workflows",
        prompt="The font on the settings page looks slightly off-center on mobile",
        response_matches=[r"(?i)(font|mobile|css|ui|alignment|layout|setting)"],
        response_not_contains=["Traceback", "ESC-", "CRITICAL"],
        max_duration=120.0,
    ),
]
