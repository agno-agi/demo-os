"""CLI entry point: python -m agents.helpdesk"""

from agents.helpdesk.agent import helpdesk

if __name__ == "__main__":
    helpdesk.cli_app(stream=True)
