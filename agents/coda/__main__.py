"""CLI entry point: python -m agents.coda"""

from agents.coda.team import coda

if __name__ == "__main__":
    coda.cli_app(stream=True)
