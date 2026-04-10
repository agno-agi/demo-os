"""CLI entry point: python -m agents.approvals"""

from agents.approvals.agent import approvals

if __name__ == "__main__":
    approvals.cli_app(stream=True)
