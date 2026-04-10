"""CLI entry point: python -m agents.scheduler"""

from agents.scheduler.agent import scheduler

if __name__ == "__main__":
    scheduler.cli_app(stream=True)
