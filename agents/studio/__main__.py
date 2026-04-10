"""CLI entry point: python -m agents.studio"""

from agents.studio.agent import studio

if __name__ == "__main__":
    studio.cli_app(stream=True)
