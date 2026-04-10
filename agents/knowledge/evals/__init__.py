"""
Knowledge Agent Evaluation Suite.

Usage:
    python -m agents.knowledge.evals.run_evals                    # String matching (default)
    python -m agents.knowledge.evals.run_evals --llm-grader       # LLM-based grading
"""

from agents.knowledge.evals.grader import GradeResult, grade_response
from agents.knowledge.evals.test_cases import CATEGORIES, TEST_CASES, TestCase

__all__ = [
    "TEST_CASES",
    "CATEGORIES",
    "TestCase",
    "grade_response",
    "GradeResult",
]
