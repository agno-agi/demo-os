"""
Dash Evaluations
================

Eval framework for testing Dash's capabilities.

Usage:
    python -m evals
    python -m evals --category security
    python -m evals --verbose
"""

from agno.models.openai import OpenAIResponses

JUDGE_MODEL = OpenAIResponses(id="gpt-5.4")


CATEGORIES: dict[str, dict] = {
    "accuracy": {"type": "accuracy", "module": "agents.dash.evals.test_cases"},
}
