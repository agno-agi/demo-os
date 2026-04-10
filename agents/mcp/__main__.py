"""CLI entry point: python -m agents.mcp"""

from agents.mcp.agent import mcp_agent

if __name__ == "__main__":
    mcp_agent.cli_app(stream=True)
