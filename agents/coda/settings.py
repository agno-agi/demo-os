"""Shared settings for Coda agents."""

from os import getenv
from pathlib import Path

from agno.models.openai import OpenAIResponses

from db import create_knowledge, get_postgres_db

agent_db = get_postgres_db()
REPOS_DIR = Path(getenv("REPOS_DIR", "/repos"))
MODEL = OpenAIResponses(id="gpt-5.4")
coda_learnings = create_knowledge("Coda Learnings", "coda_learnings")
