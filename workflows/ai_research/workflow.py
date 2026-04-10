"""AI Research - Daily parallel AI research workflow."""

from agno.agent import Agent
from agno.tools.parallel import ParallelTools
from agno.workflow import Step, Workflow
from agno.workflow.parallel import Parallel

from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools
from workflows.ai_research.instructions import (
    INDUSTRY_INSTRUCTIONS,
    INFRA_INSTRUCTIONS,
    MODELS_INSTRUCTIONS,
    PRODUCTS_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
)

models_agent = Agent(
    name="AI Models & Releases",
    model=MODEL,
    db=agent_db,
    tools=[ParallelTools(), *get_exa_mcp_tools("web_search_exa")],
    instructions=MODELS_INSTRUCTIONS,
)

products_agent = Agent(
    name="AI Products & Startups",
    model=MODEL,
    db=agent_db,
    tools=[ParallelTools(), *get_exa_mcp_tools("web_search_exa,company_research_exa")],
    instructions=PRODUCTS_INSTRUCTIONS,
)

infra_agent = Agent(
    name="AI Infrastructure",
    model=MODEL,
    db=agent_db,
    tools=[ParallelTools(), *get_exa_mcp_tools("web_search_exa,get_code_context_exa")],
    instructions=INFRA_INSTRUCTIONS,
)

industry_agent = Agent(
    name="AI Policy & Industry",
    model=MODEL,
    db=agent_db,
    tools=[ParallelTools(), *get_exa_mcp_tools("web_search_exa")],
    instructions=INDUSTRY_INSTRUCTIONS,
)

synthesizer = Agent(
    name="Research Synthesizer",
    model=MODEL,
    db=agent_db,
    instructions=SYNTHESIZER_INSTRUCTIONS,
    markdown=True,
)

ai_research = Workflow(
    id="ai-research",
    name="AI Research",
    steps=[
        Parallel(
            Step(name="Models & Releases", agent=models_agent),  # type: ignore[arg-type]
            Step(name="Products & Startups", agent=products_agent),  # type: ignore[arg-type]
            Step(name="Infrastructure", agent=infra_agent),  # type: ignore[arg-type]
            Step(name="Policy & Industry", agent=industry_agent),  # type: ignore[arg-type]
            name="Parallel Research",
        ),
        Step(name="Synthesize", agent=synthesizer),
    ],
)
