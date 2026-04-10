"""
Test cases for evaluating the Knowledge agent.

Each test case includes:
- question: The natural language question to ask
- expected_strings: Strings that should appear in the response
- category: Test category for filtering
"""

from dataclasses import dataclass


@dataclass
class TestCase:
    """A test case for evaluating the Knowledge agent."""

    question: str
    expected_strings: list[str]
    category: str


TEST_CASES: list[TestCase] = [
    # Concepts - questions about Agno framework concepts
    TestCase(
        question="What is Agno?",
        expected_strings=["agent", "framework"],
        category="concepts",
    ),
    TestCase(
        question="What model providers does Agno support?",
        expected_strings=["OpenAI", "Anthropic"],
        category="concepts",
    ),
    TestCase(
        question="What is a Knowledge base in Agno?",
        expected_strings=["knowledge", "vector", "RAG"],
        category="concepts",
    ),
    TestCase(
        question="How does Agno handle memory?",
        expected_strings=["memory", "session"],
        category="concepts",
    ),
    # Implementation - how-to questions requiring code examples
    TestCase(
        question="How do I create a basic agent in Agno?",
        expected_strings=["Agent", "import", "model"],
        category="implementation",
    ),
    TestCase(
        question="How do I add tools to an Agno agent?",
        expected_strings=["tools", "Agent"],
        category="implementation",
    ),
    TestCase(
        question="How do I set up a Knowledge base with PgVector?",
        expected_strings=["PgVector", "Knowledge", "embedder"],
        category="implementation",
    ),
    TestCase(
        question="How do I use MCP tools with an Agno agent?",
        expected_strings=["MCP", "MCPTools"],
        category="implementation",
    ),
    # Edge cases - ambiguous or boundary questions
    TestCase(
        question="Can Agno agents use LangChain tools?",
        expected_strings=["tool"],
        category="edge_case",
    ),
    TestCase(
        question="What is the maximum context window for Agno?",
        expected_strings=["model"],
        category="edge_case",
    ),
    TestCase(
        question="How does Agno compare to CrewAI?",
        expected_strings=["agent"],
        category="edge_case",
    ),
]

# Categories for filtering
CATEGORIES = ["concepts", "implementation", "edge_case"]
