"""
LLM-based grader for evaluating Knowledge agent responses.

Uses a small, fast model to evaluate if the agent's response correctly
answers questions about the Agno framework documentation.
"""

from dataclasses import dataclass

from openai import OpenAI


@dataclass
class GradeResult:
    """Result of LLM grading."""

    passed: bool
    reasoning: str
    score: float  # 0.0 to 1.0


GRADER_SYSTEM_PROMPT = """\
You are an evaluation grader for an Agno documentation agent. Your job is to determine if the agent's
response correctly answers the user's question about the Agno framework.

You will be given:
1. The user's question
2. The agent's response
3. Expected values that should appear in the answer

Evaluate based on:
- Factual correctness: Does the response contain accurate information about Agno?
- Completeness: Does it answer the question asked?
- Code quality: If code is included, is it correct and runnable?
- No hallucinations: The response should not include made-up features or APIs.

Be lenient about:
- Extra context or insights (the agent may provide more than asked)
- Different phrasing or formatting
- Additional details beyond what was expected

Respond in this exact format:
SCORE: [0.0-1.0]
PASSED: [true/false]
REASONING: [brief explanation]
"""


def grade_response(
    question: str,
    response: str,
    expected_values: list[str],
    model: str = "gpt-5-mini",
) -> GradeResult:
    """
    Use an LLM to grade the agent's response.

    Args:
        question: The original question asked
        response: The agent's response text
        expected_values: List of strings that should appear in the response
        model: The model to use for grading

    Returns:
        GradeResult with pass/fail, score, and reasoning
    """
    client = OpenAI()

    expected_context = f"Expected values to appear: {', '.join(expected_values)}" if expected_values else ""

    user_message = f"""\
Question: {question}

Agent Response:
{response}

Expected Answer:
{expected_context}

Grade this response."""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": GRADER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=500,
    )

    grader_response = completion.choices[0].message.content or ""
    return _parse_grade_response(grader_response)


def _parse_grade_response(response: str) -> GradeResult:
    """Parse the grader's response into a GradeResult."""
    lines = response.strip().split("\n")

    score = 0.5
    passed = False
    reasoning = "Could not parse grader response"

    for line in lines:
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("PASSED:"):
            passed_str = line.split(":", 1)[1].strip().lower()
            passed = passed_str == "true"
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    return GradeResult(passed=passed, reasoning=reasoning, score=score)
