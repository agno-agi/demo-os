"""CLI entry point: python -m agents.docs"""

from agents.docs.agent import docs_agent

if __name__ == "__main__":
    docs_agent.cli_app(stream=True)
