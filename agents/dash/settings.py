"""
Shared settings for Dash agents.

Centralizes the database, model, knowledge bases, and learning config
so all agents share the same resources.
"""

from os import getenv

from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.models.openai import OpenAIResponses

from db import create_knowledge, get_postgres_db

# Database
agent_db = get_postgres_db()

# Model — full object, not just ID.
# Change class + ID together when switching providers.
MODEL = OpenAIResponses(id="gpt-5.4")

# Slack
SLACK_TOKEN = getenv("SLACK_TOKEN", "")
SLACK_SIGNING_SECRET = getenv("SLACK_SIGNING_SECRET", "")

# Dual knowledge system
# KNOWLEDGE: Static, curated (table schemas, validated queries, business rules)
dash_knowledge = create_knowledge("Dash Knowledge", "dash_knowledge")
# LEARNINGS: Dynamic, discovered (error patterns, gotchas, user corrections)
dash_learnings = create_knowledge("Dash Learnings", "dash_learnings")

# Shared learning machine — single instance used by leader + all members.
dash_learning = LearningMachine(
    knowledge=dash_learnings,
    learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
)
