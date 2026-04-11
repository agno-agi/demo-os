"""
Craftsman - Skills Demo Agent
=============================

Demonstrates Agno's Skills system:
- ``Skills`` — skill manager that loads and serves skills
- ``LocalSkills`` — loader for skills stored on the local filesystem
- SKILL.md + scripts/ + references/ directory structure

The ``skills=`` parameter automatically registers ``get_skill_instructions``,
``get_skill_reference``, and ``get_skill_script`` as agent tools.
"""

from pathlib import Path

from agno.agent import Agent
from agno.skills import LocalSkills, Skills

from agents.craftsman.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

SKILLS_DIR = Path(__file__).parent / "skills"

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
craftsman = Agent(
    id="craftsman",
    name="Craftsman",
    model=MODEL,
    db=agent_db,
    skills=Skills(loaders=[LocalSkills(path=str(SKILLS_DIR))]),
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
