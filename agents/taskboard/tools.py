"""Taskboard tools — session state manipulation for task management."""

from agno.agent import Agent
from agno.tools import tool


@tool
def add_task(
    agent: Agent,
    title: str,
    priority: str = "medium",
    category: str = "general",
    due_date: str = "",
) -> str:
    """Add a new task to the taskboard.

    Args:
        title: Short description of the task.
        priority: low, medium, or high.
        category: general, work, or personal.
        due_date: Optional due date in YYYY-MM-DD format.
    """
    state = agent.session_state or {}
    tasks = state.get("tasks", [])
    task_id = f"T-{len(tasks) + 1:03d}"
    tasks.append(
        {
            "id": task_id,
            "title": title,
            "priority": priority,
            "category": category,
            "status": "todo",
            "due_date": due_date,
        }
    )
    agent.update_session_state({"tasks": tasks})
    return f"Added {task_id}: {title} [priority={priority}, category={category}]"


@tool
def update_task_status(agent: Agent, task_id: str, status: str) -> str:
    """Update the status of a task.

    Args:
        task_id: The task identifier (e.g., T-001).
        status: New status — todo, in_progress, done, or cancelled.
    """
    state = agent.session_state or {}
    tasks = state.get("tasks", [])
    for task in tasks:
        if task["id"] == task_id:
            old_status = task["status"]
            task["status"] = status
            agent.update_session_state({"tasks": tasks})
            return f"{task_id} updated: {old_status} → {status}"
    return f"Task {task_id} not found."


@tool
def list_tasks(agent: Agent, status: str = "", category: str = "") -> str:
    """List tasks, optionally filtered by status or category.

    Args:
        status: Filter by status (todo, in_progress, done, cancelled). Leave empty for all.
        category: Filter by category (general, work, personal). Leave empty for all.
    """
    state = agent.session_state or {}
    tasks = state.get("tasks", [])
    if not tasks:
        return "No tasks on the board."

    filtered = tasks
    if status:
        filtered = [t for t in filtered if t["status"] == status]
    if category:
        filtered = [t for t in filtered if t["category"] == category]

    if not filtered:
        return "No tasks match the filter."

    lines = [
        "| ID | Title | Priority | Category | Status | Due |",
        "|----|-------|----------|----------|--------|-----|",
    ]
    for t in filtered:
        lines.append(
            f"| {t['id']} | {t['title']} | {t['priority']} | {t['category']} | {t['status']} | {t.get('due_date', '')} |"
        )
    return "\n".join(lines)


@tool
def remove_task(agent: Agent, task_id: str) -> str:
    """Remove a task from the taskboard.

    Args:
        task_id: The task identifier to remove (e.g., T-001).
    """
    state = agent.session_state or {}
    tasks = state.get("tasks", [])
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            removed = tasks.pop(i)
            agent.update_session_state({"tasks": tasks})
            return f"Removed {task_id}: {removed['title']}"
    return f"Task {task_id} not found."


@tool
def get_summary(agent: Agent) -> str:
    """Get a summary of all tasks by status and category."""
    state = agent.session_state or {}
    tasks = state.get("tasks", [])
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

    high_priority = [t for t in tasks if t["priority"] == "high" and t["status"] in ("todo", "in_progress")]
    if high_priority:
        lines.append("")
        lines.append("**High-priority open tasks:**")
        for t in high_priority:
            lines.append(f"- {t['id']}: {t['title']} ({t['status']})")

    return "\n".join(lines)
