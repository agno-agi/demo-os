"""
Navigator Agent
===============

The primary agent users interact with. Handles email, calendar,
SQL, files, web research, and wiki-aware Q&A.

Reads the wiki index first for knowledge questions, then pulls
specific articles. Falls back to raw/ and live sources.
"""

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.models.openai import OpenAIResponses

from agents.pal.instructions import build_navigator_instructions
from agents.pal.settings import agent_db, pal_knowledge, pal_learnings
from agents.pal.tools import build_navigator_tools

navigator = Agent(
    id="navigator",
    name="Navigator",
    role="Primary agent for user interaction, knowledge queries, email, calendar, SQL, files, and wiki Q&A",
    model=OpenAIResponses(id="gpt-5.4"),
    db=agent_db,
    instructions=build_navigator_instructions(),
    knowledge=pal_knowledge,
    search_knowledge=True,
    learning=LearningMachine(
        knowledge=pal_learnings,
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
    tools=build_navigator_tools(pal_knowledge),
    enable_agentic_memory=True,
    search_past_sessions=True,
    num_past_sessions_to_search=5,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=10,
    markdown=True,
)
