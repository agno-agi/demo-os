from agno.agent import Agent
from agno.learn import (
    EntityMemoryConfig,
    LearningMachine,
    LearningMode,
    SessionContextConfig,
    UserProfileConfig,
)

from agents.contacts.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
contacts = Agent(
    id="contacts",
    name="Contacts",
    model=MODEL,
    db=agent_db,
    learning=LearningMachine(
        user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
        entity_memory=EntityMemoryConfig(
            mode=LearningMode.AGENTIC,
            enable_create_entity=True,
            enable_add_fact=True,
            enable_add_relationship=True,
            enable_add_event=True,
        ),
        session_context=SessionContextConfig(
            mode=LearningMode.ALWAYS,
            enable_planning=True,
        ),
    ),
    tools=[*get_exa_mcp_tools()],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
