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

from agents.dash import dash, dash_knowledge, dash_learnings
from agents.helpdesk import helpdesk
from agents.mcp import mcp_agent
from agents.reasoner import reasoner
from agents.reporter import reporter
from agents.studio import studio
from agents.taskboard import taskboard
from app.registry import registry
from app.settings import RUNTIME_ENV, SCHEDULER_BASE_URL, SLACK_SIGNING_SECRET, SLACK_TOKEN, agent_db
from frameworks.claude_repo import claude_repo
from frameworks.dspy_math import dspy_math
from frameworks.langgraph_debate import langgraph_debate
from teams.investment import (
    investment_broadcast,
    investment_coordinate,
    investment_knowledge,
    investment_learnings,
    investment_route,
    investment_tasks,
)
from teams.research import research_coordinate
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
        helpdesk,
        reasoner,
        reporter,
        studio,
        taskboard,
        claude_repo,  # type: ignore[list-item]
        langgraph_debate,  # type: ignore[list-item]
        dspy_math,  # type: ignore[list-item]
    ],
    teams=[
        dash,
        research_coordinate,
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
        investment_knowledge,
        investment_learnings,
    ],
    interfaces=interfaces,
    registry=registry,
    config=str(Path(__file__).parent / "config.yaml"),
)

app = agent_os.get_app()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
# Register a lightweight /health route that bypasses the main database
# connection pool entirely.  WebSocket connections to /workflows/ws can hold
# pool slots open for minutes; if the pool is exhausted the default AgentOS
# health endpoint hangs waiting for a connection and the load-balancer marks
# the instance unhealthy.  This override returns 200 immediately — if the
# process is alive and accepting requests, it is healthy.
#
# The route is inserted at the front of the router's route list so it takes
# precedence over any /health route that AgentOS may have already registered.
@app.get("/health", include_in_schema=False, tags=["ops"])
async def health_check() -> dict[str, str]:
    """Lightweight liveness probe — never touches the database."""
    return {"status": "ok"}


# Move the route we just appended to position 0 so it shadows any previously
# registered /health handler (FastAPI matches routes in registration order).
app.routes.insert(0, app.routes.pop())


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
