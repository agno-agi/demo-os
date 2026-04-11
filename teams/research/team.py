from agno.agent import Agent
from agno.team import Team, TeamMode

from app.settings import MODEL, agent_db, get_parallel_tools
from teams.research.instructions import (
    ANALYST_INSTRUCTIONS,
    BROADCAST_INSTRUCTIONS,
    COORDINATE_INSTRUCTIONS,
    INVESTIGATOR_INSTRUCTIONS,
    ROUTE_INSTRUCTIONS,
    TASKS_INSTRUCTIONS,
    WRITER_INSTRUCTIONS,
)
from utils.exa import get_exa_mcp_tools

# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------
analyst = Agent(
    id="research-analyst",
    name="Analyst",
    role="Data analysis, market sizing, trends, quantitative research",
    model=MODEL,
    db=agent_db,
    tools=[*get_parallel_tools(), *get_exa_mcp_tools("web_search_exa")],
    instructions=ANALYST_INSTRUCTIONS,
    add_datetime_to_context=True,
    markdown=True,
)

investigator = Agent(
    id="research-investigator",
    name="Investigator",
    role="Company/people research, competitive intelligence",
    model=MODEL,
    db=agent_db,
    tools=[*get_parallel_tools(), *get_exa_mcp_tools("web_search_exa,company_research_exa,people_search_exa")],
    instructions=INVESTIGATOR_INSTRUCTIONS,
    add_datetime_to_context=True,
    markdown=True,
)

writer = Agent(
    id="research-writer",
    name="Writer",
    role="Synthesis, reports, structured output",
    model=MODEL,
    db=agent_db,
    instructions=WRITER_INSTRUCTIONS,
    add_datetime_to_context=True,
    markdown=True,
)

members: list[Agent | Team] = [analyst, investigator, writer]

# ---------------------------------------------------------------------------
# Create Teams
# ---------------------------------------------------------------------------
research_coordinate = Team(
    id="research-coordinate",
    name="Research Team (Coordinate)",
    mode=TeamMode.coordinate,
    model=MODEL,
    members=members,
    db=agent_db,
    instructions=COORDINATE_INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    markdown=True,
)

research_route = Team(
    id="research-route",
    name="Research Team (Route)",
    mode=TeamMode.route,
    model=MODEL,
    members=members,
    db=agent_db,
    instructions=ROUTE_INSTRUCTIONS,
    add_datetime_to_context=True,
    markdown=True,
)

research_broadcast = Team(
    id="research-broadcast",
    name="Research Team (Broadcast)",
    mode=TeamMode.broadcast,
    model=MODEL,
    members=members,
    db=agent_db,
    instructions=BROADCAST_INSTRUCTIONS,
    add_datetime_to_context=True,
    markdown=True,
)

research_tasks = Team(
    id="research-tasks",
    name="Research Team (Tasks)",
    mode=TeamMode.tasks,
    model=MODEL,
    members=members,
    db=agent_db,
    instructions=TASKS_INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    markdown=True,
)
