"""
Registry for the Demo AgentOS.

Provides shared tools, models, and database connections for AgentOS.
"""

from agno.models.openai import OpenAIResponses
from agno.registry import Registry
from agno.tools.parallel import ParallelTools

from app.settings import MODEL, agent_db

registry = Registry(
    tools=[ParallelTools()],
    models=[MODEL, OpenAIResponses(id="gpt-5.4-mini")],
    dbs=[agent_db],
)
