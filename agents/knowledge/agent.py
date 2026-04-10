"""
Knowledge - Agno Documentation Agent
=====================================

RAG-based Q&A agent that searches embedded Agno documentation using
hybrid vector + keyword search. Answers developer questions about the
Agno framework with working code examples.

Run:
    python -m agents.knowledge
"""

from agno.agent import Agent

from agents.knowledge.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db
from db import create_knowledge

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
knowledge = create_knowledge("Knowledge Agent", "agno_knowledge_agent_docs")

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
knowledge_agent = Agent(
    id="knowledge",
    name="Knowledge",
    model=MODEL,
    db=agent_db,
    knowledge=knowledge,
    instructions=INSTRUCTIONS,
    search_knowledge=True,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)


def load_agno_documentation() -> None:
    """Load Agno documentation into the knowledge base."""
    knowledge.insert(
        name="Agno llms-full.txt",
        url="https://docs.agno.com/llms-full.txt",
        skip_if_exists=True,
    )
    knowledge.insert(
        name="Agno llms.txt",
        url="https://docs.agno.com/llms.txt",
        skip_if_exists=True,
    )
