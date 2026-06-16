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

from agents.approvals import approvals
from agents.dash import dash, dash_knowledge, dash_learnings
from agents.mcp import mcp_agent
from agents.reporter import reporter
from agents.studio import studio
from agents.taskboard import taskboard
from agents.travel import travel
from app.registry import registry
from app.settings import RUNTIME_ENV, SCHEDULER_BASE_URL, SLACK_SIGNING_SECRET, SLACK_TOKEN, agent_db
from frameworks.claude_repo import claude_repo
from frameworks.dspy_math import dspy_math
from frameworks.langgraph_debate import langgraph_debate
from teams.clinic import clinic, clinic_knowledge
from teams.coach import coach_learnings, coach_team
from teams.investment import (
    investment_broadcast,
    investment_knowledge,
    investment_learnings,
)
from teams.research import research_coordinate
from workflows.ai_research import ai_research
from workflows.content_pipeline import content_pipeline
from workflows.morning_brief import morning_brief
from workflows.repo_walkthrough import repo_walkthrough
from workflows.support_bot import support_bot
from workflows.support_triage import support_triage

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
    yield


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
    db=agent_db,
    agents=[
        mcp_agent,
        travel,
        approvals,
        reporter,
        studio,
        taskboard,
        claude_repo,  # type: ignore[list-item]
        langgraph_debate,  # type: ignore[list-item]
        dspy_math,  # type: ignore[list-item]
    ],
    teams=[
        dash,
        coach_team,
        clinic,
        investment_broadcast,
        research_coordinate,
    ],
    workflows=[
        morning_brief,
        ai_research,
        content_pipeline,
        repo_walkthrough,
        support_triage,
        support_bot,
    ],
    knowledge=[
        dash_knowledge,
        dash_learnings,
        investment_knowledge,
        investment_learnings,
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
        name="dawn",
        cron="0 8 * * 1-5",
        endpoint="/workflows/dawn/runs",
        payload={"message": "Generate my morning briefing."},
        timezone="America/New_York",
        description="Weekday morning briefing",
        if_exists="update",
    )
    mgr.create(
        name="pulse",
        cron="0 7 * * *",
        endpoint="/workflows/pulse/runs",
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
