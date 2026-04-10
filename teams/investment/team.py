"""Investment Team — 7 agents across 4 team modes."""

from __future__ import annotations

from os import getenv
from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.team import Team, TeamMode
from agno.tools.file import FileTools
from agno.tools.yfinance import YFinanceTools

from app.settings import MODEL, agent_db
from db import create_knowledge
from teams.investment.instructions import (
    BROADCAST_INSTRUCTIONS,
    COMMITTEE_CHAIR_INSTRUCTIONS,
    COORDINATE_INSTRUCTIONS,
    FINANCIAL_ANALYST_INSTRUCTIONS,
    KNOWLEDGE_AGENT_INSTRUCTIONS,
    MARKET_ANALYST_INSTRUCTIONS,
    MEMO_WRITER_INSTRUCTIONS,
    RISK_OFFICER_INSTRUCTIONS,
    ROUTE_INSTRUCTIONS,
    TASKS_INSTRUCTIONS,
    TECHNICAL_ANALYST_INSTRUCTIONS,
)
from utils.exa import get_exa_mcp_tools

# ---------------------------------------------------------------------------
# Shared settings
# ---------------------------------------------------------------------------

investment_knowledge = create_knowledge("Investment Knowledge", "investment_knowledge")
investment_learnings = create_knowledge("Investment Learnings", "investment_learnings")

MEMOS_DIR = Path(__file__).parent / "memos"

_learning = LearningMachine(
    knowledge=investment_learnings,
    learned_knowledge=LearnedKnowledgeConfig(
        mode=LearningMode.AGENTIC,
        namespace="global",
    ),
)

_common: dict[str, Any] = dict(
    db=agent_db,
    knowledge=investment_knowledge,
    search_knowledge=True,
    learning=_learning,
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
    enable_agentic_memory=True,
)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
financial_analyst = Agent(
    id="investment-financial-analyst",
    name="Financial Analyst",
    role="Fundamental valuation, balance sheet, and earnings analysis",
    model=MODEL,
    instructions=FINANCIAL_ANALYST_INSTRUCTIONS,
    tools=[YFinanceTools()],
    **_common,
)

market_analyst_tools: list = [*get_exa_mcp_tools("web_search_exa"), YFinanceTools()]
if getenv("PARALLEL_API_KEY"):
    from agno.tools.parallel import ParallelTools

    market_analyst_tools.append(ParallelTools())

market_analyst = Agent(
    id="investment-market-analyst",
    name="Market Analyst",
    role="Macro environment, sector trends, and breaking news",
    model=MODEL,
    instructions=MARKET_ANALYST_INSTRUCTIONS,
    tools=market_analyst_tools,
    **_common,
)

technical_analyst = Agent(
    id="investment-technical-analyst",
    name="Technical Analyst",
    role="Price action, momentum indicators, and entry/exit timing",
    model=MODEL,
    instructions=TECHNICAL_ANALYST_INSTRUCTIONS,
    tools=[YFinanceTools()],
    **_common,
)

risk_officer = Agent(
    id="investment-risk-officer",
    name="Risk Officer",
    role="Downside scenarios, position sizing, and mandate compliance",
    model=MODEL,
    instructions=RISK_OFFICER_INSTRUCTIONS,
    tools=[YFinanceTools()],
    **_common,
)

knowledge_agent = Agent(
    id="investment-knowledge-agent",
    name="Knowledge Agent",
    role="Team librarian — research RAG and memo archive navigation",
    model=MODEL,
    instructions=KNOWLEDGE_AGENT_INSTRUCTIONS,
    tools=[
        FileTools(
            base_dir=MEMOS_DIR,
            enable_read_file=True,
            enable_list_files=True,
            enable_search_files=True,
            enable_save_file=False,
            enable_delete_file=False,
        )
    ],
    **_common,
)

memo_writer = Agent(
    id="investment-memo-writer",
    name="Memo Writer",
    role="Synthesize analyst inputs into formal investment memos",
    model=MODEL,
    db=agent_db,
    instructions=MEMO_WRITER_INSTRUCTIONS,
    tools=[
        FileTools(
            base_dir=MEMOS_DIR,
            enable_save_file=True,
            enable_read_file=True,
            enable_list_files=True,
            enable_search_files=True,
            enable_delete_file=False,
        )
    ],
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
    enable_agentic_memory=True,
)

committee_chair = Agent(
    id="investment-committee-chair",
    name="Committee Chair",
    role="Final decision-maker and capital allocator",
    model=MODEL,
    instructions=COMMITTEE_CHAIR_INSTRUCTIONS,
    **_common,
)

# ---------------------------------------------------------------------------
# Teams (4 modes)
# ---------------------------------------------------------------------------
_core_members: list[Agent | Team] = [market_analyst, financial_analyst, technical_analyst, risk_officer]
_full_members: list[Agent | Team] = [*_core_members, knowledge_agent, memo_writer]

investment_coordinate = Team(
    id="investment-coordinate",
    name="Investment Team (Coordinate)",
    mode=TeamMode.coordinate,
    model=MODEL,
    members=_full_members,
    db=agent_db,
    instructions=COORDINATE_INSTRUCTIONS,
    learning=_learning,
    enable_agentic_memory=True,
    show_members_responses=True,
    add_datetime_to_context=True,
    markdown=True,
)

investment_route = Team(
    id="investment-route",
    name="Investment Team (Route)",
    mode=TeamMode.route,
    model=MODEL,
    members=[*_full_members, committee_chair],
    db=agent_db,
    instructions=ROUTE_INSTRUCTIONS,
    show_members_responses=True,
    add_datetime_to_context=True,
    markdown=True,
)

investment_broadcast = Team(
    id="investment-broadcast",
    name="Investment Team (Broadcast)",
    mode=TeamMode.broadcast,
    model=MODEL,
    members=_core_members,
    db=agent_db,
    instructions=BROADCAST_INSTRUCTIONS,
    learning=_learning,
    enable_agentic_memory=True,
    show_members_responses=True,
    add_datetime_to_context=True,
    markdown=True,
)

investment_tasks = Team(
    id="investment-tasks",
    name="Investment Team (Tasks)",
    mode=TeamMode.tasks,
    model=MODEL,
    members=_full_members,
    db=agent_db,
    instructions=TASKS_INSTRUCTIONS,
    learning=_learning,
    enable_agentic_memory=True,
    show_members_responses=True,
    add_datetime_to_context=True,
    markdown=True,
)
