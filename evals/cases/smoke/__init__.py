"""Smoke test case definitions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SmokeTest:
    """A single smoke test case."""

    id: str
    name: str
    entity_type: str  # "agent" | "team" | "workflow"
    entity_id: str
    group: str  # "agents" | "teams" | "workflows" | "security" | "graceful"
    prompt: str
    response_contains: list[str] = field(default_factory=list)
    response_not_contains: list[str] = field(default_factory=list)
    response_matches: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    timeout: float = 120.0
    max_duration: float | None = None


def all_smoke_tests() -> list[SmokeTest]:
    """Return all smoke test cases across all groups."""
    from evals.cases.smoke.agents import AGENT_TESTS
    from evals.cases.smoke.graceful import GRACEFUL_TESTS
    from evals.cases.smoke.hitl import HITL_TESTS
    from evals.cases.smoke.security import SECURITY_TESTS
    from evals.cases.smoke.teams import TEAM_TESTS
    from evals.cases.smoke.workflows import WORKFLOW_TESTS

    return AGENT_TESTS + TEAM_TESTS + WORKFLOW_TESTS + SECURITY_TESTS + GRACEFUL_TESTS + HITL_TESTS
