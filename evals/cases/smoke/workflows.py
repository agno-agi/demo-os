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
        entity_id="daily-brief",
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
        entity_id="ai-digest",
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
        entity_id="scribe",
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
        entity_id="code-scout",
        group="workflows",
        prompt="Walk me through the Dash codebase",
        response_matches=[r"(?i)(dash|code|agent|team|analyst)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    # -------------------------------------------------------------------------
    # Classifier (classify -> route to specialist -> conditional deep analysis)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.5",
        name="classifier — routes a paper to the arxiv specialist",
        entity_type="workflow",
        entity_id="classifier",
        group="workflows",
        prompt="Summarize this paper: arxiv.org/abs/1706.03762",
        response_matches=[r"(?i)(attention|transformer|paper|abstract|arxiv)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    SmokeTest(
        id="w.5.2",
        name="classifier — routes a topic to the encyclopedia specialist",
        entity_type="workflow",
        entity_id="classifier",
        group="workflows",
        prompt="Explain the topic: retrieval-augmented generation",
        response_matches=[r"(?i)(retrieval|generation|rag|wikipedia|explain)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    SmokeTest(
        id="w.5.3",
        name="classifier — quick topic does not deep-dive",
        entity_type="workflow",
        entity_id="classifier",
        group="workflows",
        prompt="In one line, what is HTTP?",
        response_matches=[r"(?i)(http|protocol|web|hypertext)"],
        response_not_contains=["Traceback"],
        max_duration=120.0,
    ),
    # -------------------------------------------------------------------------
    # Support Bot (step-level HITL — pauses to collect environment)
    # -------------------------------------------------------------------------
    SmokeTest(
        id="w.6",
        name="support-bot — pauses to collect environment (step-level HITL)",
        entity_type="workflow",
        entity_id="troubleshooter",
        group="workflows",
        prompt="ModuleNotFoundError: No module named 'agno.workflow.types'",
        response_matches=[r"(?i)(agno_version|python_version|environment|setup|version)"],
        response_not_contains=["Traceback"],
        max_duration=90.0,
    ),
]
