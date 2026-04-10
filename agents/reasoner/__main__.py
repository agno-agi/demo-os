"""CLI entry point: python -m agents.reasoner"""

from agents.reasoner.agent import reasoner

if __name__ == "__main__":
    reasoner.cli_app(stream=True)
