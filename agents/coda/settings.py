"""Shared settings for Coda agents."""

from os import getenv
from pathlib import Path

from app.settings import MODEL  # noqa: F401 — re-exported for agents
from db import create_knowledge, get_postgres_db

agent_db = get_postgres_db()
REPOS_DIR = Path(getenv("REPOS_DIR", "/repos"))
coda_learnings = create_knowledge("Coda Learnings", "coda_learnings")


def get_github_tools(include_tools: list[str]) -> list:
    """Return GithubTools if a GitHub token is available, else empty list."""
    if getenv("GITHUB_TOKEN") or getenv("GITHUB_ACCESS_TOKEN"):
        from agno.tools.github import GithubTools

        return [GithubTools(include_tools=include_tools)]
    return []
