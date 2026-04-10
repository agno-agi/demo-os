"""
MCP Agent Evaluation Suite.

Usage:
    python -m agents.mcp.evals.run_evals                    # String matching (default)
    python -m agents.mcp.evals.run_evals --llm-grader       # LLM-based grading
"""

from agents.mcp.evals.grader import GradeResult, grade_response
from agents.mcp.evals.test_cases import CATEGORIES, TEST_CASES, TestCase

__all__ = [
    "TEST_CASES",
    "CATEGORIES",
    "TestCase",
    "grade_response",
    "GradeResult",
]
