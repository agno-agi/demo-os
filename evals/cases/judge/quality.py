"""
Quality Judge Eval
==================

Numeric judge: evaluates response quality on completeness, structure,
actionability, and conciseness. Applied to entities producing long-form output.
"""

CRITERIA = (
    "Evaluate the response quality on these dimensions:\n"
    "1. COMPLETENESS: Does it fully address the question?\n"
    "2. STRUCTURE: Is it well-organized with clear sections or logical flow?\n"
    "3. ACTIONABILITY: Does it provide concrete, useful information?\n"
    "4. CONCISENESS: Is it appropriately detailed without padding or filler?\n"
    "Score 1-10. A score of 7+ means the response is good across all dimensions.\n"
    "Score below 7 if it is vague, disorganized, padded, or incomplete."
)

CASES = [
    "Give me a detailed analysis of the pros and cons of microservices vs monolith architecture",
    "Research the latest developments in AI agents and summarize key trends",
    "Write a technical comparison of PostgreSQL vs MongoDB for a startup",
]

ENTITIES: list[tuple[str, str]] = [
    ("team", "research-coordinate"),
]
