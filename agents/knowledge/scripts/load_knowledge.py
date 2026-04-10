"""
Load Agno documentation into the Knowledge agent's knowledge base.

Usage:
    python -m agents.knowledge.scripts.load_knowledge
"""

if __name__ == "__main__":
    from agents.knowledge.agent import load_agno_documentation

    print("Loading Agno documentation into knowledge base...\n")
    load_agno_documentation()
    print("\nDone!")
