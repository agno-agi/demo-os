"""CLI entry point: python -m agents.dash"""

from agents.dash.team import dash

if __name__ == "__main__":
    dash.cli_app(stream=True)
