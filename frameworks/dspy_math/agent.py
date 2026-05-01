"""
Math Solver (DSPy)
==================

A DSPy ChainOfThought agent that solves word problems with step-by-step
reasoning. Uses a typed signature so the output is always structured as
numbered steps followed by the final answer.

Demonstrates: serving a DSPy program through AgentOS.
"""

import dspy
from agno.agents.dspy import DSPyAgent

from app.settings import agent_db

dspy.configure(lm=dspy.LM("openai/gpt-5.4"))


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------
class WordProblem(dspy.Signature):
    """Solve a math word problem with explicit step-by-step reasoning."""

    problem: str = dspy.InputField(desc="A math word problem in plain English.")
    solution: str = dspy.OutputField(
        desc=(
            "The full solution as markdown: numbered reasoning steps followed by a "
            "**Final Answer:** line with the numeric result and units."
        )
    )


# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
dspy_math = DSPyAgent(
    id="dspy-math",
    name="Math Solver (DSPy)",
    description="Solves word problems step-by-step using DSPy's ChainOfThought.",
    db=agent_db,
    program=dspy.ChainOfThought(WordProblem),
    input_field="problem",
    output_field="solution",
    markdown=True,
)
