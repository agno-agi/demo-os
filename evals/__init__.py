"""
Agno Demo Evaluations
=====================

Eval framework for testing agent capabilities across the demo.

Usage:
    python -m evals
    python -m evals --category security
    python -m evals --verbose
"""

from dataclasses import dataclass

from agno.models.openai import OpenAIResponses

JUDGE_MODEL = OpenAIResponses(id="gpt-5.4")


@dataclass
class TestCase:
    """A test case for per-agent evaluations."""

    question: str
    expected_strings: list[str]
    expected_tools: list[str]
    category: str


CATEGORIES: dict[str, dict] = {
    "security": {"type": "judge_binary", "module": "evals.cases.security"},
}
