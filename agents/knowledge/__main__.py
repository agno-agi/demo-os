"""CLI entry point: python -m agents.knowledge"""

from agents.knowledge.agent import knowledge_agent

if __name__ == "__main__":
    knowledge_agent.cli_app(stream=True)
