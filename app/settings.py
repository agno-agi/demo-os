"""
Shared Settings
---------------

Centralizes the model, database, and environment flags
so all agents share the same resources.
"""

from os import getenv

from agno.models.openai import OpenAIResponses

from db import get_postgres_db

# Database — single instance shared by all agents
agent_db = get_postgres_db()

# Model — change class + ID together when switching providers
MODEL = OpenAIResponses(id="gpt-5.4")

# Environment
RUNTIME_ENV = getenv("RUNTIME_ENV", "prd")
SLACK_TOKEN = getenv("SLACK_TOKEN", "")
SLACK_SIGNING_SECRET = getenv("SLACK_SIGNING_SECRET", "")
