"""CLI entry point: python -m agents.feedback"""

from agents.feedback.agent import feedback

if __name__ == "__main__":
    feedback.cli_app(stream=True)
