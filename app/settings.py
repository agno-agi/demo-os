"""
Shared Settings
===============

Centralizes the model, database, and environment flags
so all agents share the same resources.
"""

from os import getenv

from agno.models.openai import OpenAIResponses

from db import get_postgres_db

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
agent_db = get_postgres_db()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
MODEL = OpenAIResponses(id="gpt-5.5")

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
RUNTIME_ENV = getenv("RUNTIME_ENV", "prd")
SCHEDULER_BASE_URL = getenv("AGENTOS_URL", "http://127.0.0.1:8000")
SLACK_TOKEN = getenv("SLACK_TOKEN", "")
SLACK_SIGNING_SECRET = getenv("SLACK_SIGNING_SECRET", "")

# ---------------------------------------------------------------------------
# Usage limits
# ---------------------------------------------------------------------------
USAGE_LIMITS_ENABLED = getenv("USAGE_LIMITS_ENABLED", "true").lower() in ("1", "true", "yes")
USER_RATE_LIMIT_RPM = int(getenv("USER_RATE_LIMIT_RPM", "10"))
USER_DAILY_RUN_LIMIT = int(getenv("USER_DAILY_RUN_LIMIT", "50"))

# ---------------------------------------------------------------------------
# Optional tools
# ---------------------------------------------------------------------------
PARALLEL_API_KEY = getenv("PARALLEL_API_KEY", "")


def get_parallel_tools(**kwargs) -> list:
    """Return ParallelTools if PARALLEL_API_KEY is set, else empty list."""
    if PARALLEL_API_KEY:
        from agno.tools.parallel import ParallelTools

        return [ParallelTools(**kwargs)]
    return []
