"""CLI entry point: python -m agents.contacts"""

from agents.contacts.agent import contacts

if __name__ == "__main__":
    contacts.cli_app(stream=True)
