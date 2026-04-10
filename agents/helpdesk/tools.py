"""
Helpdesk - Human-in-the-Loop tools.

Demonstrates all three HITL patterns in Agno:
1. requires_confirmation  - Operator must approve before execution
2. requires_user_input    - User provides additional input at runtime
3. external_execution     - Command runs outside the agent runtime

All tools return simulated responses for demo purposes.
"""

from agno.tools import tool


@tool(requires_confirmation=True)
def restart_service(service_name: str) -> str:
    """Restart a running service. Requires operator confirmation before executing.

    Args:
        service_name: Name of the service to restart (e.g. 'auth-api', 'payments-api').

    Returns:
        Status message confirming the restart.
    """
    return f"Service '{service_name}' has been restarted successfully. New PID: 48291. Uptime: 0s."


@tool(requires_user_input=True, user_input_fields=["priority"])
def create_support_ticket(title: str, description: str, priority: str = "medium") -> str:
    """Create a support ticket. The user will be prompted to confirm the priority level.

    Args:
        title: Short title for the ticket.
        description: Detailed description of the issue.
        priority: Priority level (low, medium, high, critical). User confirms this value.

    Returns:
        Confirmation with the ticket ID.
    """
    ticket_id = f"TKT-{abs(hash(title)) % 10000:04d}"
    return (
        f"Support ticket created:\n"
        f"  ID: {ticket_id}\n"
        f"  Title: {title}\n"
        f"  Priority: {priority}\n"
        f"  Description: {description}"
    )


@tool(external_execution=True)
def run_diagnostic(command: str) -> str:
    """Run a diagnostic command on the infrastructure. The command is executed outside the agent runtime.

    Args:
        command: The diagnostic command to run (e.g. 'health-check payments-api').

    Returns:
        Diagnostic output.
    """
    return (
        f"Diagnostic results for '{command}':\n"
        f"  Status: healthy\n"
        f"  Latency: 42ms\n"
        f"  CPU: 23%\n"
        f"  Memory: 512MB / 2GB\n"
        f"  Active connections: 147"
    )
