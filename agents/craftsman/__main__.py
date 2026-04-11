"""CLI entry point: python -m agents.craftsman"""

from agents.craftsman.agent import craftsman

if __name__ == "__main__":
    craftsman.cli_app(stream=True)
