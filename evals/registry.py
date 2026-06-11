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
    "sage": Entity(
        id="sage",
        type="agent",
        instruction_file="agents/mcp/instructions.py",
        definition_file="agents/mcp/agent.py",
    ),
    "glass": Entity(
        id="glass",
        type="agent",
        instruction_file="agents/helpdesk/instructions.py",
        definition_file="agents/helpdesk/agent.py",
    ),
    "ledger": Entity(
        id="ledger",
        type="agent",
        instruction_file="agents/approvals/instructions.py",
        definition_file="agents/approvals/agent.py",
    ),
    "quill": Entity(
        id="quill",
        type="agent",
        instruction_file="agents/reporter/instructions.py",
        definition_file="agents/reporter/agent.py",
        requires=["EXA_API_KEY"],
    ),
    "iris": Entity(
        id="iris",
        type="agent",
        instruction_file="agents/studio/instructions.py",
        definition_file="agents/studio/agent.py",
    ),
    "pilot": Entity(
        id="pilot",
        type="agent",
        instruction_file="agents/taskboard/instructions.py",
        definition_file="agents/taskboard/agent.py",
    ),
    # -------------------------------------------------------------------------
    # Teams (6)
    # -------------------------------------------------------------------------
    "dash": Entity(
        id="dash",
        type="team",
        instruction_file="agents/dash/instructions.py",
        definition_file="agents/dash/team.py",
    ),
    "atlas": Entity(
        id="atlas",
        type="team",
        instruction_file="teams/research/instructions.py",
        definition_file="teams/research/team.py",
        requires=["EXA_API_KEY"],
    ),
    "quorum": Entity(
        id="quorum",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    "switch": Entity(
        id="switch",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    "chorus": Entity(
        id="chorus",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    "foreman": Entity(
        id="foreman",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    # -------------------------------------------------------------------------
    # Workflows (5)
    # -------------------------------------------------------------------------
    "dawn": Entity(
        id="dawn",
        type="workflow",
        instruction_file="workflows/morning_brief/instructions.py",
        definition_file="workflows/morning_brief/workflow.py",
    ),
    "pulse": Entity(
        id="pulse",
        type="workflow",
        instruction_file="workflows/ai_research/instructions.py",
        definition_file="workflows/ai_research/workflow.py",
        requires=["EXA_API_KEY"],
    ),
    "press": Entity(
        id="press",
        type="workflow",
        instruction_file="workflows/content_pipeline/instructions.py",
        definition_file="workflows/content_pipeline/workflow.py",
    ),
    "echo": Entity(
        id="echo",
        type="workflow",
        instruction_file="workflows/repo_walkthrough/instructions.py",
        definition_file="workflows/repo_walkthrough/workflow.py",
    ),
    "beacon": Entity(
        id="beacon",
        type="workflow",
        instruction_file="workflows/support_triage/instructions.py",
        definition_file="workflows/support_triage/workflow.py",
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
