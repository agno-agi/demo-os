"""Shared settings for Coda agents."""

from os import getenv
from pathlib import Path
from typing import List

from agno.models.openai import OpenAIResponses

from db import create_knowledge, get_postgres_db

agent_db = get_postgres_db()
REPOS_DIR = Path(getenv("REPOS_DIR", "/repos"))
MODEL = OpenAIResponses(id="gpt-5.4")
coda_learnings = create_knowledge("Coda Learnings", "coda_learnings")


def get_github_tools(include_tools: List[str]) -> list:
    """Return GithubTools if a GitHub token is available, else empty list."""
    if getenv("GITHUB_TOKEN") or getenv("GITHUB_ACCESS_TOKEN"):
        from agno.tools.github import GithubTools

        return [GithubTools(include_tools=include_tools)]
    return []
