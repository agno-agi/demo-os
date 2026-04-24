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

from agents.approvals import approvals
from agents.compressor import compressor
from agents.contacts import contacts
from agents.craftsman import craftsman
from agents.dash import dash, dash_knowledge, dash_learnings
from agents.docs import docs_agent
from agents.feedback import feedback
from agents.helpdesk import helpdesk
from agents.injector import injector
from agents.mcp import mcp_agent
from agents.pal import pal, pal_knowledge, pal_learnings
from agents.reasoner import reasoner
from agents.reporter import reporter
from agents.scheduler import scheduler
from agents.studio import studio
from agents.taskboard import taskboard
from app.registry import registry
from app.settings import RUNTIME_ENV, SCHEDULER_BASE_URL, SLACK_SIGNING_SECRET, SLACK_TOKEN, agent_db
from teams.investment import (
    investment_broadcast,
    investment_coordinate,
    investment_knowledge,
    investment_learnings,
    investment_route,
    investment_tasks,
)
from teams.research import research_broadcast, research_coordinate, research_route, research_tasks
from workflows.ai_research import ai_research
from workflows.content_pipeline import content_pipeline
from workflows.morning_brief import morning_brief
from workflows.repo_walkthrough import repo_walkthrough
from workflows.support_triage import support_triage

# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------
interfaces: list = []
if SLACK_TOKEN and SLACK_SIGNING_SECRET:
    from agno.os.interfaces.slack import Slack

    interfaces.append(
        Slack(
            agent=docs_agent,
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
    lifespan=lifespan,
    db=agent_db,
    agents=[
        docs_agent,
        mcp_agent,
        helpdesk,
        feedback,
        approvals,
        reasoner,
        reporter,
        contacts,
        studio,
        scheduler,
        taskboard,
        compressor,
        injector,
        craftsman,
    ],
    teams=[
        pal,
        dash,
        research_coordinate,
        research_route,
        research_broadcast,
        research_tasks,
        investment_coordinate,
        investment_route,
        investment_broadcast,
        investment_tasks,
    ],
    workflows=[
        morning_brief,
        ai_research,
        content_pipeline,
        repo_walkthrough,
        support_triage,
    ],
    knowledge=[
        dash_knowledge,
        dash_learnings,
        pal_knowledge,
        pal_learnings,
        investment_knowledge,
        investment_learnings,
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
        name="morning-brief",
        cron="0 8 * * 1-5",
        endpoint="/workflows/morning-brief/runs",
        payload={"message": "Generate my morning briefing."},
        timezone="America/New_York",
        description="Weekday morning briefing",
        if_exists="update",
    )
    mgr.create(
        name="ai-research",
        cron="0 7 * * *",
        endpoint="/workflows/ai-research/runs",
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
