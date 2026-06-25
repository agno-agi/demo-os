"""
Operator - Infrastructure change tools.

Threads three Agno features through one task, in a single turn:
1. draft_plan              - returns a typed, risk-scored ChangePlan (structured output)
2. apply_change            - requires_confirmation=True (human-in-the-loop pause before execution)
3. @approval(type="required") - blocking admin approval; a pending record is created for the run

The plan is the typed return value of a tool (not the agent's response schema) so the
approval gate on ``apply_change`` can pause the run in the same turn the plan is drafted.

All cloud operations are mocked — nothing leaves the process. The agent reasons over a small
simulated inventory to ground each plan's blast radius and risk.
"""

from typing import List, Literal

from agno.approval import approval
from agno.tools import tool
from pydantic import BaseModel, Field

Action = Literal["scale", "destroy", "rotate", "apply"]


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------
class BlastRadius(BaseModel):
    """How far the change reaches, and what is affected, if it goes wrong."""

    environment: str = Field(..., description="Target environment, e.g. 'production' or 'staging'.")
    scope: str = Field(..., description="One line describing what is affected and how widely.")
    reversible: bool = Field(..., description="Whether the change can be cleanly rolled back.")


class ChangePlan(BaseModel):
    """A typed, risk-scored infrastructure change plan."""

    resource: str = Field(..., description="The resource the change targets, e.g. 'web-cluster'.")
    action: Action = Field(..., description="The kind of change being made.")
    blast_radius: BlastRadius = Field(..., description="What is affected if the change goes wrong.")
    affected_services: List[str] = Field(
        default_factory=list, description="Downstream services impacted by the change."
    )
    rollback_steps: List[str] = Field(default_factory=list, description="Ordered steps to undo the change if needed.")
    risk: Literal["low", "medium", "high"] = Field(
        ..., description="Overall risk. 'high' drives the destructive/audit approval path."
    )


# ---------------------------------------------------------------------------
# Simulated inventory
# ---------------------------------------------------------------------------
# A small mock fleet so the agent can ground its plans in concrete state. Each
# entry records what depends on the resource (for blast radius) and whether it
# holds state (stateful destroys are inherently high risk).
INVENTORY: dict[str, dict] = {
    "web-cluster": {
        "kind": "kubernetes-deployment",
        "env": "production",
        "replicas": 4,
        "max_replicas": 12,
        "stateful": False,
        "depends_on": ["checkout-api", "storefront"],
    },
    "orders-db": {
        "kind": "postgres-instance",
        "env": "production",
        "replicas": 1,
        "max_replicas": 1,
        "stateful": True,
        "latest_snapshot": "snap-orders-db-2026-06-23-0200 (verified, 3.2 GB)",
        "depends_on": ["checkout-api", "orders-api", "analytics"],
    },
    "cache-redis": {
        "kind": "redis-instance",
        "env": "staging",
        "replicas": 2,
        "max_replicas": 6,
        "stateful": False,
        "depends_on": ["storefront"],
    },
    "payments-api-key": {
        "kind": "credential",
        "env": "production",
        "replicas": 0,
        "max_replicas": 0,
        "stateful": True,
        "depends_on": ["checkout-api", "billing-worker"],
    },
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@tool
def inspect_resource(resource: str) -> str:
    """Inspect the current (simulated) state of a resource before drafting a plan.

    Returns the resource's state and the services that depend on it, so you can reason
    about blast radius, rollback, and risk. Call this first when you need details about a
    resource you have not seen in this conversation.

    Args:
        resource: Resource identifier (e.g. 'web-cluster', 'orders-db', 'payments-api-key').

    Returns:
        A human-readable snapshot of the resource state and its downstream dependents.
    """
    res = INVENTORY.get(resource)
    if res is None:
        known = ", ".join(sorted(INVENTORY))
        return f"Unknown resource '{resource}'. Known resources: {known}."

    dependents = ", ".join(res["depends_on"]) or "none"
    snapshot = res.get("latest_snapshot", "none on record")
    return (
        f"Resource: {resource}\n"
        f"  Kind: {res['kind']}\n"
        f"  Environment: {res['env']}\n"
        f"  Current replicas: {res['replicas']} (max {res['max_replicas']})\n"
        f"  Stateful: {res['stateful']}\n"
        f"  Latest snapshot: {snapshot}\n"
        f"  Downstream dependents: {dependents}\n"
        f"  Note: stateful destroys and production credential rotations are high risk; "
        f"scaling within max is usually low to medium."
    )


@tool
def draft_plan(plan: ChangePlan) -> ChangePlan:
    """Record the change plan you have drafted. Returns the typed, validated ChangePlan.

    Build the plan from the resource state and your skills (read Terraform state, run the
    incident-runbook blast-radius check) before calling this. Always call this before
    ``apply_change`` so there is a typed plan on record to approve.

    Args:
        plan: The complete ChangePlan — resource, action, blast radius, affected services,
            ordered rollback steps, and an honest risk rating.

    Returns:
        The same plan, validated against the ChangePlan schema.
    """
    return plan


@approval(type="required")  # type: ignore[call-overload]
@tool(requires_confirmation=True)
def apply_change(resource: str, action: Action, summary: str) -> str:
    """Submit a drafted change for rollout. Gated by a blocking human approval.

    Call this right after ``draft_plan`` to request approval. This is a blocking approval:
    the run pauses and a pending entry appears in the Approvals view for this run, which a
    human must approve before the change is cleared for rollout. If the human rejects, the
    change does not proceed.

    Args:
        resource: Resource identifier the plan targets.
        action: The action to execute — one of 'scale', 'destroy', 'rotate', 'apply'.
        summary: One-line summary of what the plan does.

    Returns:
        Approval status with a change record reference. Simulated — no real infrastructure is touched.
    """
    res = INVENTORY.get(resource, {})
    env = res.get("env", "unknown")
    ref = f"CHG-{abs(hash(resource + action)) % 100000:05d}"
    return (
        f"Plan approved.\n"
        f"  Reference record: {ref}\n"
        f"  Resource: {resource} ({env})\n"
        f"  Action: {action}\n"
        f"  Summary: {summary}\n"
        f"  Approval: granted through the blocking approval gate\n"
        f"  Status: approved for rollout"
    )
