"""
Entity Registry
================

Single source of truth for all eval targets.

Every eval module imports from here. Adding a new entity means adding
one entry to ENTITIES. Everything else derives from it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    """An agent, team, or workflow that can be evaluated."""

    id: str
    type: str  # "agent" | "team" | "workflow"
    instruction_file: str  # relative to project root
    definition_file: str  # relative to project root
    requires: list[str] = field(default_factory=list)  # env vars needed to run


ENTITIES: dict[str, Entity] = {
    # -------------------------------------------------------------------------
    # Agents (6)
    # -------------------------------------------------------------------------
    "agno-expert": Entity(
        id="agno-expert",
        type="agent",
        instruction_file="agents/mcp/instructions.py",
        definition_file="agents/mcp/agent.py",
    ),
    "voyager": Entity(
        id="voyager",
        type="agent",
        instruction_file="agents/travel/instructions.py",
        definition_file="agents/travel/agent.py",
    ),
    "operator": Entity(
        id="operator",
        type="agent",
        instruction_file="agents/infra/instructions.py",
        definition_file="agents/infra/agent.py",
    ),
    "researcher": Entity(
        id="researcher",
        type="agent",
        instruction_file="agents/reporter/instructions.py",
        definition_file="agents/reporter/agent.py",
        requires=["EXA_API_KEY"],
    ),
    "media-lab": Entity(
        id="media-lab",
        type="agent",
        instruction_file="agents/studio/instructions.py",
        definition_file="agents/studio/agent.py",
    ),
    "planner": Entity(
        id="planner",
        type="agent",
        instruction_file="agents/taskboard/instructions.py",
        definition_file="agents/taskboard/agent.py",
    ),
    # -------------------------------------------------------------------------
    # Teams
    # -------------------------------------------------------------------------
    "dash": Entity(
        id="dash",
        type="team",
        instruction_file="agents/dash/instructions.py",
        definition_file="agents/dash/team.py",
    ),
    "clinic": Entity(
        id="clinic",
        type="team",
        instruction_file="teams/clinic/instructions.py",
        definition_file="teams/clinic/team.py",
    ),
    "newsroom": Entity(
        id="newsroom",
        type="team",
        instruction_file="teams/research/instructions.py",
        definition_file="teams/research/team.py",
        requires=["EXA_API_KEY"],
    ),
    # -------------------------------------------------------------------------
    # Workflows (5)
    # -------------------------------------------------------------------------
    "daily-brief": Entity(
        id="daily-brief",
        type="workflow",
        instruction_file="workflows/morning_brief/instructions.py",
        definition_file="workflows/morning_brief/workflow.py",
    ),
    "ai-digest": Entity(
        id="ai-digest",
        type="workflow",
        instruction_file="workflows/ai_research/instructions.py",
        definition_file="workflows/ai_research/workflow.py",
        requires=["EXA_API_KEY"],
    ),
    "scribe": Entity(
        id="scribe",
        type="workflow",
        instruction_file="workflows/content_pipeline/instructions.py",
        definition_file="workflows/content_pipeline/workflow.py",
    ),
    "code-scout": Entity(
        id="code-scout",
        type="workflow",
        instruction_file="workflows/repo_walkthrough/instructions.py",
        definition_file="workflows/repo_walkthrough/workflow.py",
    ),
    "classifier": Entity(
        id="classifier",
        type="workflow",
        instruction_file="workflows/classifier/instructions.py",
        definition_file="workflows/classifier/workflow.py",
    ),
    "troubleshooter": Entity(
        id="troubleshooter",
        type="workflow",
        instruction_file="workflows/support_bot/instructions.py",
        definition_file="workflows/support_bot/workflow.py",
    ),
}


def get(entity_id: str) -> Entity:
    """Look up an entity by ID. Raises KeyError if not found."""
    return ENTITIES[entity_id]


def agents() -> list[Entity]:
    """All agent entities."""
    return [e for e in ENTITIES.values() if e.type == "agent"]


def teams() -> list[Entity]:
    """All team entities."""
    return [e for e in ENTITIES.values() if e.type == "team"]


def workflows() -> list[Entity]:
    """All workflow entities."""
    return [e for e in ENTITIES.values() if e.type == "workflow"]


def entity_tuples() -> list[tuple[str, str]]:
    """(entity_type, entity_id) pairs for all entities."""
    return [(e.type, e.id) for e in ENTITIES.values()]
