"""CLI entry point: python -m agents.taskboard"""

from agents.taskboard.agent import taskboard

if __name__ == "__main__":
    taskboard.cli_app(stream=True)
