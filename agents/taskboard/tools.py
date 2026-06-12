"""Taskboard tools — session state manipulation for a personal work planner."""

from datetime import date, datetime

from agno.run import RunContext
from agno.tools import tool

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
EFFORT_VALUES = ("quick", "medium", "deep")
OPEN_STATUSES = ("todo", "in_progress", "blocked", "waiting")


def _state(run_context: RunContext) -> dict:
    """Return the live session state, initializing it if empty."""
    if run_context.session_state is None:
        run_context.session_state = {}
    state = run_context.session_state
    state.setdefault("tasks", [])
    state.setdefault("categories", ["general", "work", "personal"])
    return state


def _parse_due(due_date: str) -> date | None:
    """Parse a YYYY-MM-DD due date, returning None if empty or malformed."""
    if not due_date:
        return None
    try:
        return datetime.strptime(due_date, "%Y-%m-%d").date()
    except ValueError:
        return None


def _row(t: dict) -> str:
    return (
        f"| {t['id']} | {t['title']} | {t['priority']} | {t.get('effort', 'medium')} "
        f"| {t['category']} | {t['status']} | {t.get('due_date', '') or '—'} |"
    )


def _table(tasks: list[dict]) -> str:
    lines = [
        "| ID | Title | Priority | Effort | Category | Status | Due |",
        "|----|-------|----------|--------|----------|--------|-----|",
    ]
    lines.extend(_row(t) for t in tasks)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Capture & edit
# ---------------------------------------------------------------------------
@tool
def add_task(
    run_context: RunContext,
    title: str,
    priority: str = "medium",
    category: str = "general",
    effort: str = "medium",
    due_date: str = "",
) -> str:
    """Add a new task to the planner.

    Args:
        title: Short description of the task.
        priority: low, medium, or high.
        category: general, work, or personal.
        effort: Rough size of the task — quick, medium, or deep (deep = focused/long).
        due_date: Optional due date in YYYY-MM-DD format.
    """
    state = _state(run_context)
    tasks = state["tasks"]
    task_id = f"T-{len(tasks) + 1:03d}"
    if effort not in EFFORT_VALUES:
        effort = "medium"
    tasks.append(
        {
            "id": task_id,
            "title": title,
            "priority": priority,
            "category": category,
            "effort": effort,
            "status": "todo",
            "due_date": due_date,
            "blocked_reason": "",
        }
    )
    return (
        f"Added {task_id}: {title} [priority={priority}, effort={effort}, category={category}, due={due_date or '—'}]"
    )


@tool
def update_task_status(run_context: RunContext, task_id: str, status: str, blocked_reason: str = "") -> str:
    """Update the status of a task.

    Args:
        task_id: The task identifier (e.g., T-001).
        status: New status — todo, in_progress, blocked, waiting, done, or cancelled.
        blocked_reason: When status is 'blocked' or 'waiting', what it's waiting on.
    """
    tasks = _state(run_context)["tasks"]
    for task in tasks:
        if task["id"] == task_id:
            old_status = task["status"]
            task["status"] = status
            task["blocked_reason"] = blocked_reason if status in ("blocked", "waiting") else ""
            detail = f" (waiting on: {blocked_reason})" if blocked_reason else ""
            return f"{task_id} updated: {old_status} → {status}{detail}"
    return f"Task {task_id} not found."


@tool
def remove_task(run_context: RunContext, task_id: str) -> str:
    """Remove a task from the planner.

    Args:
        task_id: The task identifier to remove (e.g., T-001).
    """
    tasks = _state(run_context)["tasks"]
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            removed = tasks.pop(i)
            return f"Removed {task_id}: {removed['title']}"
    return f"Task {task_id} not found."


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
@tool
def list_tasks(run_context: RunContext, status: str = "", category: str = "") -> str:
    """List tasks, optionally filtered by status or category.

    Args:
        status: Filter by status (todo, in_progress, blocked, waiting, done, cancelled). Leave empty for all.
        category: Filter by category (general, work, personal). Leave empty for all.
    """
    tasks = _state(run_context)["tasks"]
    if not tasks:
        return "No tasks on the board."

    filtered = tasks
    if status:
        filtered = [t for t in filtered if t["status"] == status]
    if category:
        filtered = [t for t in filtered if t["category"] == category]

    if not filtered:
        return "No tasks match the filter."
    return _table(filtered)


@tool
def agenda(run_context: RunContext) -> str:
    """Show what's due — overdue tasks and tasks due today — so the user can triage deadlines.

    Uses the system's current date as the reference, so it is always accurate.
    """
    tasks = _state(run_context)["tasks"]
    ref = date.today()

    overdue, due_today = [], []
    for t in tasks:
        if t["status"] not in OPEN_STATUSES:
            continue
        due = _parse_due(t.get("due_date", ""))
        if due is None:
            continue
        if due < ref:
            overdue.append(t)
        elif due == ref:
            due_today.append(t)

    if not overdue and not due_today:
        return "Nothing overdue and nothing due today. You're clear on deadlines."

    sections = []
    if overdue:
        overdue.sort(key=lambda t: t.get("due_date", ""))
        sections.append("**⚠️ Overdue:**\n" + _table(overdue))
    if due_today:
        sections.append("**📅 Due today:**\n" + _table(due_today))
    return "\n\n".join(sections)


@tool
def plan_my_day(run_context: RunContext) -> str:
    """Rank the open tasks into a suggested order to work them today.

    Sorts by priority, then due date (sooner first), then effort. The agent should
    layer the user's remembered work-style preferences on top of this ordering.
    """
    tasks = _state(run_context)["tasks"]
    open_tasks = [t for t in tasks if t["status"] in ("todo", "in_progress")]
    if not open_tasks:
        blocked = [t for t in tasks if t["status"] in ("blocked", "waiting")]
        if blocked:
            return "No actionable tasks — everything open is blocked or waiting:\n\n" + _table(blocked)
        return "No open tasks to plan. Add some tasks first."

    def sort_key(t: dict) -> tuple:
        due = t.get("due_date", "") or "9999-99-99"
        return (PRIORITY_RANK.get(t["priority"], 1), due, EFFORT_VALUES.index(t.get("effort", "medium")))

    ranked = sorted(open_tasks, key=sort_key)
    lines = ["**Suggested order for today:**", ""]
    for i, t in enumerate(ranked, 1):
        due = t.get("due_date", "")
        meta = f"{t['priority']} priority · {t.get('effort', 'medium')} effort"
        meta += f" · due {due}" if due else ""
        lines.append(f"{i}. **{t['title']}** ({t['id']}) — {meta}")

    blocked = [t for t in tasks if t["status"] in ("blocked", "waiting")]
    if blocked:
        lines.append("")
        lines.append("_Blocked / waiting (not scheduled):_ " + ", ".join(t["id"] for t in blocked))
    return "\n".join(lines)


@tool
def get_summary(run_context: RunContext) -> str:
    """Get a summary of all tasks by status and category, plus high-priority open work."""
    tasks = _state(run_context)["tasks"]
    if not tasks:
        return "No tasks on the board."

    by_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for t in tasks:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        by_category[t["category"]] = by_category.get(t["category"], 0) + 1

    lines = [f"**Total tasks:** {len(tasks)}", ""]
    lines.append("**By status:**")
    for s, count in by_status.items():
        lines.append(f"- {s}: {count}")
    lines.append("")
    lines.append("**By category:**")
    for c, count in by_category.items():
        lines.append(f"- {c}: {count}")

    high_priority = [t for t in tasks if t["priority"] == "high" and t["status"] in OPEN_STATUSES]
    if high_priority:
        lines.append("")
        lines.append("**High-priority open tasks:**")
        for t in high_priority:
            lines.append(f"- {t['id']}: {t['title']} ({t['status']})")

    return "\n".join(lines)
