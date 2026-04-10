"""
Test cases for evaluating the MCP agent.

Each test case includes:
- question: The natural language question to ask
- expected_strings: Strings that should appear in the response
- category: Test category for filtering
"""

from dataclasses import dataclass


@dataclass
class TestCase:
    """A test case for evaluating the MCP agent."""

    question: str
    expected_strings: list[str]
    category: str


TEST_CASES: list[TestCase] = [
    # Concepts - questions about Agno framework concepts via MCP
    TestCase(
        question="What is Agno?",
        expected_strings=["agent", "framework"],
        category="concepts",
    ),
    TestCase(
        question="What is AgentOS?",
        expected_strings=["AgentOS", "agent"],
        category="concepts",
    ),
    TestCase(
        question="What are Teams in Agno?",
        expected_strings=["team", "agent"],
        category="concepts",
    ),
    # Implementation - how-to questions requiring tool lookups
    TestCase(
        question="How do I create a custom tool in Agno?",
        expected_strings=["tool", "def"],
        category="implementation",
    ),
    TestCase(
        question="How do I connect to an MCP server in Agno?",
        expected_strings=["MCP", "url"],
        category="implementation",
    ),
    TestCase(
        question="How do I set up a workflow in Agno?",
        expected_strings=["Workflow"],
        category="implementation",
    ),
    TestCase(
        question="How do I use structured outputs with an Agno agent?",
        expected_strings=["response_model"],
        category="implementation",
    ),
    # Edge cases - boundary and unusual questions
    TestCase(
        question="Can I use Agno with a local Ollama model?",
        expected_strings=["Ollama"],
        category="edge_case",
    ),
    TestCase(
        question="What happens if an MCP server is unavailable?",
        expected_strings=["error"],
        category="edge_case",
    ),
    TestCase(
        question="Does Agno support streaming responses?",
        expected_strings=["stream"],
        category="edge_case",
    ),
]

# Categories for filtering
CATEGORIES = ["concepts", "implementation", "edge_case"]
