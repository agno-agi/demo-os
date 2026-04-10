"""CLI entry point: python -m agents.reporter"""

from agents.reporter.agent import reporter

if __name__ == "__main__":
    reporter.cli_app(stream=True)
