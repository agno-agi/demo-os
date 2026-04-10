"""CLI entry point: python -m agents.pal"""

from agents.pal.team import pal

if __name__ == "__main__":
    pal.cli_app(stream=True)
