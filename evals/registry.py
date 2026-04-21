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
    # Agents (14)
    # -------------------------------------------------------------------------
    "docs": Entity(
        id="docs",
        type="agent",
        instruction_file="agents/docs/instructions.py",
        definition_file="agents/docs/agent.py",
    ),
    "mcp": Entity(
        id="mcp",
        type="agent",
        instruction_file="agents/mcp/instructions.py",
        definition_file="agents/mcp/agent.py",
    ),
    "helpdesk": Entity(
        id="helpdesk",
        type="agent",
        instruction_file="agents/helpdesk/instructions.py",
        definition_file="agents/helpdesk/agent.py",
    ),
    "feedback": Entity(
        id="feedback",
        type="agent",
        instruction_file="agents/feedback/instructions.py",
        definition_file="agents/feedback/agent.py",
    ),
    "approvals": Entity(
        id="approvals",
        type="agent",
        instruction_file="agents/approvals/instructions.py",
        definition_file="agents/approvals/agent.py",
    ),
    "reasoner": Entity(
        id="reasoner",
        type="agent",
        instruction_file="agents/reasoner/instructions.py",
        definition_file="agents/reasoner/agent.py",
    ),
    "reporter": Entity(
        id="reporter",
        type="agent",
        instruction_file="agents/reporter/instructions.py",
        definition_file="agents/reporter/agent.py",
        requires=["EXA_API_KEY"],
    ),
    "contacts": Entity(
        id="contacts",
        type="agent",
        instruction_file="agents/contacts/instructions.py",
        definition_file="agents/contacts/agent.py",
    ),
    "studio": Entity(
        id="studio",
        type="agent",
        instruction_file="agents/studio/instructions.py",
        definition_file="agents/studio/agent.py",
    ),
    "scheduler": Entity(
        id="scheduler",
        type="agent",
        instruction_file="agents/scheduler/instructions.py",
        definition_file="agents/scheduler/agent.py",
    ),
    "taskboard": Entity(
        id="taskboard",
        type="agent",
        instruction_file="agents/taskboard/instructions.py",
        definition_file="agents/taskboard/agent.py",
    ),
    "compressor": Entity(
        id="compressor",
        type="agent",
        instruction_file="agents/compressor/instructions.py",
        definition_file="agents/compressor/agent.py",
    ),
    "injector": Entity(
        id="injector",
        type="agent",
        instruction_file="agents/injector/instructions.py",
        definition_file="agents/injector/agent.py",
    ),
    "craftsman": Entity(
        id="craftsman",
        type="agent",
        instruction_file="agents/craftsman/instructions.py",
        definition_file="agents/craftsman/agent.py",
    ),
    # -------------------------------------------------------------------------
    # Teams (11)
    # -------------------------------------------------------------------------
    "pal": Entity(
        id="pal",
        type="team",
        instruction_file="agents/pal/instructions.py",
        definition_file="agents/pal/team.py",
    ),
    "dash": Entity(
        id="dash",
        type="team",
        instruction_file="agents/dash/instructions.py",
        definition_file="agents/dash/team.py",
    ),
    "research-coordinate": Entity(
        id="research-coordinate",
        type="team",
        instruction_file="teams/research/instructions.py",
        definition_file="teams/research/team.py",
        requires=["EXA_API_KEY"],
    ),
    "research-route": Entity(
        id="research-route",
        type="team",
        instruction_file="teams/research/instructions.py",
        definition_file="teams/research/team.py",
        requires=["EXA_API_KEY"],
    ),
    "research-broadcast": Entity(
        id="research-broadcast",
        type="team",
        instruction_file="teams/research/instructions.py",
        definition_file="teams/research/team.py",
        requires=["EXA_API_KEY"],
    ),
    "research-tasks": Entity(
        id="research-tasks",
        type="team",
        instruction_file="teams/research/instructions.py",
        definition_file="teams/research/team.py",
        requires=["EXA_API_KEY"],
    ),
    "investment-coordinate": Entity(
        id="investment-coordinate",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    "investment-route": Entity(
        id="investment-route",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    "investment-broadcast": Entity(
        id="investment-broadcast",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    "investment-tasks": Entity(
        id="investment-tasks",
        type="team",
        instruction_file="teams/investment/instructions.py",
        definition_file="teams/investment/team.py",
        requires=["EXA_API_KEY"],
    ),
    # -------------------------------------------------------------------------
    # Workflows (5)
    # -------------------------------------------------------------------------
    "morning-brief": Entity(
        id="morning-brief",
        type="workflow",
        instruction_file="workflows/morning_brief/instructions.py",
        definition_file="workflows/morning_brief/workflow.py",
    ),
    "ai-research": Entity(
        id="ai-research",
        type="workflow",
        instruction_file="workflows/ai_research/instructions.py",
        definition_file="workflows/ai_research/workflow.py",
        requires=["EXA_API_KEY"],
    ),
    "content-pipeline": Entity(
        id="content-pipeline",
        type="workflow",
        instruction_file="workflows/content_pipeline/instructions.py",
        definition_file="workflows/content_pipeline/workflow.py",
    ),
    "repo-walkthrough": Entity(
        id="repo-walkthrough",
        type="workflow",
        instruction_file="workflows/repo_walkthrough/instructions.py",
        definition_file="workflows/repo_walkthrough/workflow.py",
    ),
    "support-triage": Entity(
        id="support-triage",
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
