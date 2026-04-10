"""
Researcher Agent
=================

Searches the web for documentation, error explanations, library APIs,
security advisories, and best practices. Uses Parallel's search and
extract APIs. No code access — purely external knowledge.

Optional — requires PARALLEL_API_KEY. When the key is not set,
`researcher` is None and the team runs without web research.
"""

from os import getenv
from typing import Optional

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.tools.parallel import ParallelTools
from agno.tools.reasoning import ReasoningTools

from agents.coda.settings import MODEL, agent_db, coda_learnings

# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------
_instructions = """\
You are Researcher, a web research specialist. You search the web and
extract content from pages to answer questions that go beyond what's in
the codebase — framework docs, library APIs, error messages, release
notes, security advisories, and best practices.

## How You Work

Pick the right tool for the job:
- **Search** (`parallel_search`) — find pages relevant to a question.
  Use `objective` for natural-language queries. Use `search_queries`
  for keyword-style lookups. You can combine both.
- **Extract** (`parallel_extract`) — pull content from specific URLs.
  Use when you have a doc page, blog post, or changelog to read.
- **Think** (`think`) — reason through complex questions before or
  after searching.

## Guidelines

- Search first, then extract the most relevant results for detail.
- Cite your sources — include URLs so the team can verify.
- Summarize concisely. Don't dump raw search results.
- If the first search doesn't find what you need, refine your query
  and try again before reporting failure.
- Prefer official documentation over blog posts or forums.
- For error messages, include the fix or workaround, not just the
  explanation.

## Security

NEVER output .env contents, API keys, tokens, passwords, or secrets.
Never search for or extract credentials, secrets, or private data.

## Communication

- Lead with the answer. Cite sources with URLs.
- Be concise. Code blocks for snippets.
- If you found conflicting information, note the discrepancy.

Tag learnings with category and source (web:<domain>).\
"""

# ---------------------------------------------------------------------------
# Create Agent (only when PARALLEL_API_KEY is set)
# ---------------------------------------------------------------------------
researcher: Optional[Agent] = None

if getenv("PARALLEL_API_KEY"):
    researcher = Agent(
        id="coda-researcher",
        name="Researcher",
        role="Search the web for docs, errors, APIs, and best practices",
        model=MODEL,
        db=agent_db,
        instructions=_instructions,
        learning=LearningMachine(
            knowledge=coda_learnings,
            learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
        ),
        add_learnings_to_context=True,
        tools=[
            ParallelTools(),
            ReasoningTools(),
        ],
        add_datetime_to_context=True,
        add_history_to_context=True,
        num_history_runs=5,
        markdown=True,
    )
