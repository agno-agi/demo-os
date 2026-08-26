"""
Demo AgentOS
============

The main entry point for Demo AgentOS.

Run:
    python -m app.main
"""

from contextlib import asynccontextmanager
from pathlib import Path

from agno.os import AgentOS
from agno.os.config import AuthorizationConfig
from fastapi import FastAPI

from agents.builder import builder
from agents.dash import dash, dash_knowledge, dash_learnings
from agents.infra import infra
from agents.mcp import mcp_agent
from agents.reporter import reporter
from agents.studio import studio
from agents.taskboard import taskboard
from agents.travel import travel
from app.registry import registry
from app.settings import (
    POSTHOG_API_KEY,
    POSTHOG_HOST,
    RUNTIME_ENV,
    SCHEDULER_BASE_URL,
    SLACK_SIGNING_SECRET,
    SLACK_TOKEN,
    USAGE_LIMITS_ENABLED,
    USER_DAILY_RUN_LIMIT,
    USER_RATE_LIMIT_RPM,
    USER_TOTAL_RUN_LIMIT,
    agent_db,
)
from app.usage import UsageGate, UsageLimitMiddleware, UsageLimits, WebSocketUsageLimitMiddleware
from frameworks.claude_repo import claude_repo
from frameworks.dspy_math import dspy_math
from frameworks.langgraph_debate import langgraph_debate
from teams.clinic import clinic, clinic_knowledge
from teams.coach import coach_learnings, coach_team
from teams.research import research_coordinate
from workflows.ai_research import ai_research
from workflows.classifier import classifier
from workflows.content_pipeline import content_pipeline
from workflows.repo_walkthrough import repo_walkthrough
from workflows.support_bot import support_bot

# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------
interfaces: list = []
if SLACK_TOKEN and SLACK_SIGNING_SECRET:
    from agno.os.interfaces.slack import Slack

    interfaces.append(
        Slack(
            agent=mcp_agent,
            streaming=True,
            token=SLACK_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET,
            resolve_user_identity=True,
        )
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):  # type: ignore[no-untyped-def]
    _register_schedules()
    if usage_gate is not None:
        usage_gate.prepare()
    yield


# ---------------------------------------------------------------------------
# Base App
# ---------------------------------------------------------------------------
# Per-user usage limits on run execution. The HTTP middleware must run after
# the JWT middleware (which sets request.state.user_id) — AgentOS stacks its
# own middleware on top of base_app, so pre-adding it here gives that order.
# Workflow runs from the UI arrive as messages on /workflows/ws, which HTTP
# middleware never sees — the WebSocket middleware covers that surface with
# the same gate so both drain the same counters.
base_app = FastAPI()
usage_gate: UsageGate | None = None
if USAGE_LIMITS_ENABLED:
    usage_gate = UsageGate(
        limits=UsageLimits(
            rpm=USER_RATE_LIMIT_RPM,
            daily=USER_DAILY_RUN_LIMIT,
            total=USER_TOTAL_RUN_LIMIT,
        ),
        posthog_api_key=POSTHOG_API_KEY,
        posthog_host=POSTHOG_HOST,
    )
    base_app.add_middleware(UsageLimitMiddleware, gate=usage_gate)
    base_app.add_middleware(WebSocketUsageLimitMiddleware, gate=usage_gate)


# ---------------------------------------------------------------------------
# Create AgentOS
# ---------------------------------------------------------------------------
agent_os = AgentOS(
    name="Demo OS",
    tracing=True,
    scheduler=True,
    scheduler_base_url=SCHEDULER_BASE_URL,
    authorization=RUNTIME_ENV == "prd",
    authorization_config=AuthorizationConfig(user_isolation=True),
    lifespan=lifespan,
    base_app=base_app,
    db=agent_db,
    agents=[
        mcp_agent,
        reporter,
        builder,
        infra,
        studio,
        taskboard,
        travel,
        claude_repo,  # type: ignore[list-item]
        langgraph_debate,  # type: ignore[list-item]
        dspy_math,  # type: ignore[list-item]
    ],
    teams=[
        dash,
        coach_team,
        clinic,
        research_coordinate,
    ],
    workflows=[
        classifier,
        content_pipeline,
        repo_walkthrough,
        support_bot,
        ai_research,
    ],
    knowledge=[
        dash_knowledge,
        dash_learnings,
        clinic_knowledge,
        coach_learnings,
    ],
    interfaces=interfaces,
    registry=registry,
    config=str(Path(__file__).parent / "config.yaml"),
)

app = agent_os.get_app()


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------
def _register_schedules() -> None:
    """Register all scheduled tasks (idempotent -- safe to run on every startup)."""
    from agno.scheduler import ScheduleManager

    mgr = ScheduleManager(agent_db)
    mgr.create(
        name="ai-digest",
        cron="0 7 * * *",
        endpoint="/workflows/ai-digest/runs",
        payload={"message": "Run the daily AI research brief."},
        timezone="UTC",
        description="Daily parallel AI research",
        if_exists="update",
    )


if __name__ == "__main__":
    agent_os.serve(
        app="app.main:app",
        reload=RUNTIME_ENV == "dev",
    )
