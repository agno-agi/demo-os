"""AI Research - Daily parallel AI research workflow."""

from agno.agent import Agent
from agno.workflow import Step, Workflow
from agno.workflow.parallel import Parallel

from app.settings import MODEL, agent_db, get_parallel_tools
from utils.exa import get_exa_mcp_tools
from workflows.ai_research.instructions import (
    INDUSTRY_INSTRUCTIONS,
    INFRA_INSTRUCTIONS,
    MODELS_INSTRUCTIONS,
    PRODUCTS_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
models_agent = Agent(
    id="ai-research-models",
    name="AI Models & Releases",
    model=MODEL,
    db=agent_db,
    tools=[*get_parallel_tools(), *get_exa_mcp_tools("web_search_exa")],
    instructions=MODELS_INSTRUCTIONS,
)

products_agent = Agent(
    id="ai-research-products",
    name="AI Products & Startups",
    model=MODEL,
    db=agent_db,
    tools=[*get_parallel_tools(), *get_exa_mcp_tools("web_search_exa,company_research_exa")],
    instructions=PRODUCTS_INSTRUCTIONS,
)

infra_agent = Agent(
    id="ai-research-infra",
    name="AI Infrastructure",
    model=MODEL,
    db=agent_db,
    tools=[*get_parallel_tools(), *get_exa_mcp_tools("web_search_exa,get_code_context_exa")],
    instructions=INFRA_INSTRUCTIONS,
)

industry_agent = Agent(
    id="ai-research-industry",
    name="AI Policy & Industry",
    model=MODEL,
    db=agent_db,
    tools=[*get_parallel_tools(), *get_exa_mcp_tools("web_search_exa")],
    instructions=INDUSTRY_INSTRUCTIONS,
)

synthesizer = Agent(
    id="ai-research-synthesizer",
    name="Research Synthesizer",
    model=MODEL,
    db=agent_db,
    instructions=SYNTHESIZER_INSTRUCTIONS,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Create Workflow
# ---------------------------------------------------------------------------
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
