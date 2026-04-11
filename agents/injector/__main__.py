"""CLI entry point: python -m agents.injector"""

from agents.injector.agent import injector

if __name__ == "__main__":
    injector.cli_app(stream=True)
