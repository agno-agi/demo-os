---
name: incident-runbook
description: Escalation procedure and blast-radius checks for risky or destructive infrastructure changes. Use this before any destroy, credential rotation, or production change to decide the approval path and required sign-off.
metadata:
  domain: infrastructure
  risk: high
---

# Incident Runbook

Use this skill before any destructive action, credential rotation, or production change. It
decides the blast-radius rating and the approval path the plan must take.

## Blast-radius check

Before approving, answer three questions and record the answer in `ChangePlan.blast_radius`:

1. **Environment** — production, staging, or dev? Production multiplies risk.
2. **Scope** — how many downstream services depend on this resource? List every dependent
   in `affected_services`. Three or more is a wide blast radius.
3. **Reversible?** — is there a clean rollback (snapshot, prior config, re-issue)? If not,
   set `reversible: false` and treat the change as `high` risk.

A change is **high** blast radius if it is irreversible, touches a stateful resource, or
fans out to three or more services.

## Escalation and approval path

- **low / medium** risk → a single human confirmation before `apply_change` is enough.
- **high** risk → confirmation plus an audit-trail entry. The `apply_change` tool already
  records high-risk and destructive executions to the approval audit trail; do not bypass
  it.
- **destroy on a stateful resource** → there must be a verified snapshot, and the first
  `rollback_steps` entry must be restoring from it. Check the resource's latest snapshot
  with `inspect_resource`; if one is on record, name it in the rollback step and proceed to
  the gated approval. Only if there is genuinely no snapshot on record do you stop and
  surface that instead of asking for approval.

## Credential rotation

- Rotate by name only. Never read, echo, or log the old or new secret value.
- A production credential rotation is always at least `high` risk: dependents must pick up
  the new value, and a bad rotation can take down every service that uses it.
- Rollback for a rotation is re-issuing or re-enabling the prior credential, not printing
  it — note that in `rollback_steps` without naming any secret value.

## After approval

When the human approves, call `apply_change` once with a one-line summary. If the human
rejects, stop — no retries, no workarounds. Report that no change was made.
