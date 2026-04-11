"""
Injector - Dependency Injection Demo Agent
==========================================

Demonstrates Agno's dependency injection capabilities:
- ``dependencies`` — dict of runtime data injected at agent creation
- ``add_dependencies_to_context=True`` — dependencies visible in agent context
- ``RunContext.dependencies`` — tools access injected data via run context
"""

from agno.agent import Agent

from agents.injector.instructions import INSTRUCTIONS
from agents.injector.tools import check_feature_flag, get_config, get_user_preference
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
DEPENDENCIES = {
    "config": {
        "app_name": "AgentOS Demo",
        "version": "2.1.0",
        "max_retries": 3,
        "timeout_seconds": 30,
        "log_level": "INFO",
        "region": "us-east-1",
        "cache_ttl_minutes": 15,
        "max_upload_size_mb": 100,
    },
    "feature_flags": {
        "dark_mode": True,
        "beta_features": False,
        "advanced_analytics": True,
        "multi_language": False,
        "export_pdf": True,
        "real_time_collaboration": False,
        "ai_suggestions": True,
    },
    "user_preferences": {
        "theme": "dark",
        "language": "en",
        "notifications": True,
        "timezone": "America/New_York",
        "date_format": "YYYY-MM-DD",
        "items_per_page": 25,
    },
}

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
injector = Agent(
    id="injector",
    name="Injector",
    model=MODEL,
    db=agent_db,
    tools=[get_config, check_feature_flag, get_user_preference],
    instructions=INSTRUCTIONS,
    dependencies=DEPENDENCIES,
    add_dependencies_to_context=True,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
