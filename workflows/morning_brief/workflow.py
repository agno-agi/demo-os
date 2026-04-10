"""Morning Brief - Daily parallel briefing workflow."""

from agno.agent import Agent
from agno.tools.parallel import ParallelTools
from agno.workflow import Step, Workflow
from agno.workflow.parallel import Parallel

from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools
from workflows.morning_brief.instructions import (
    CALENDAR_INSTRUCTIONS,
    EMAIL_INSTRUCTIONS,
    NEWS_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
)
from workflows.morning_brief.tools import get_email_digest, get_todays_calendar

calendar_agent = Agent(
    name="Calendar Scanner",
    model=MODEL,
    db=agent_db,
    tools=[get_todays_calendar],
    instructions=CALENDAR_INSTRUCTIONS,
)

email_agent = Agent(
    name="Email Digester",
    model=MODEL,
    db=agent_db,
    tools=[get_email_digest],
    instructions=EMAIL_INSTRUCTIONS,
)

news_agent = Agent(
    name="News Scanner",
    model=MODEL,
    db=agent_db,
    tools=[ParallelTools(enable_extract=False), *get_exa_mcp_tools()],
    instructions=NEWS_INSTRUCTIONS,
)

synthesizer = Agent(
    name="Brief Synthesizer",
    model=MODEL,
    db=agent_db,
    instructions=SYNTHESIZER_INSTRUCTIONS,
    markdown=True,
)

morning_brief = Workflow(
    id="morning-brief",
    name="Morning Brief",
    steps=[
        Parallel(
            Step(name="Scan Calendar", agent=calendar_agent),  # type: ignore[arg-type]
            Step(name="Process Emails", agent=email_agent),  # type: ignore[arg-type]
            Step(name="Scan News", agent=news_agent),  # type: ignore[arg-type]
            name="Gather Intelligence",
        ),
        Step(name="Synthesize Brief", agent=synthesizer),
    ],
)
