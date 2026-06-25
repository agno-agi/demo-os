---
name: terraform-changes
description: How to read Terraform state, interpret a plan diff, and apply infrastructure changes safely. Use this before any scale, apply, or destroy so the change is grounded in current state and has a clear rollback.
metadata:
  domain: infrastructure
  risk: high
---

# Terraform Changes

Use this skill whenever a change touches Terraform-managed infrastructure (clusters,
databases, config). The goal is that every change is grounded in current state and has a
known rollback path before it runs.

## Read state first

1. Identify the resource and its environment. Never plan against the wrong environment.
2. Inspect current state — replica counts, instance class, whether the resource is
   stateful. A resource that holds data cannot be safely destroyed and recreated.
3. List downstream dependents. These become the plan's `affected_services`.

## Read the plan diff

A Terraform plan reports each resource as one of:

- `+ create` — additive, generally low risk.
- `~ update in-place` — usually low to medium risk; safe to roll back by re-applying the
  prior value.
- `-/+ replace` — destroy then create. Treat as high risk on anything stateful; data is
  lost between destroy and create unless a snapshot exists.
- `- destroy` — removal. High risk on shared or stateful resources.

Map the diff to a `ChangePlan.action`: a replica change is `scale`, an in-place config
change is `apply`, a `-/+` or `-` on a real resource is `destroy`.

## Safety rules

- Never `destroy` or `-/+ replace` a stateful resource without a verified snapshot in the
  rollback steps.
- Scale changes must stay within the resource's `max_replicas`. Scaling past headroom is
  not a low-risk change.
- Every plan must have ordered `rollback_steps`. If you cannot write a rollback, the risk
  is `high` and the change should be questioned, not just approved.
- Treat any production change as at least `medium` risk by default.

See `references/risk-matrix.md` for the action-to-risk mapping used to fill the
`ChangePlan.risk` field.
