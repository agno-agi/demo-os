"""Classifier - Router + Condition workflow.

Takes a single source (arXiv id, document/PDF URL, YouTube link, web article, or a topic),
classifies what KIND of source it is, routes it to the matching specialist that reads the
REAL source with real tools, and conditionally runs a deep-analysis pass for dense sources.

Demonstrates:
- ``Router`` — routes to a specialist agent based on the triager's SOURCE_TYPE
- ``Condition`` — conditionally runs deep analysis when DEPTH is "deep"
- ``StepInput`` — passing the triage classification between workflow steps

Specialists use real, mostly keyless tools (Arxiv, YouTube, Wikipedia, DuckDuckGo, Website)
plus Docling for real document (PDF/DOCX) parsing.
"""

from agno.agent import Agent
from agno.tools.arxiv import ArxivTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.website import WebsiteTools
from agno.tools.wikipedia import WikipediaTools
from agno.tools.youtube import YouTubeTools
from agno.workflow import Condition, Router, Step, Workflow
from agno.workflow.types import StepInput

from app.settings import MODEL, agent_db
from workflows.classifier.instructions import (
    ARTICLE_INSTRUCTIONS,
    DEEP_ANALYSIS_INSTRUCTIONS,
    DOCUMENT_INSTRUCTIONS,
    PAPER_INSTRUCTIONS,
    TOPIC_INSTRUCTIONS,
    TRIAGE_INSTRUCTIONS,
    VIDEO_INSTRUCTIONS,
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def _docling_tools() -> list:
    """Build DoclingTools lazily so the workflow imports even if docling isn't installed."""
    try:
        from agno.tools.docling import DoclingTools

        return [DoclingTools(enable_convert_to_markdown=True, max_chars=12000)]
    except ImportError:
        return []


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
triager = Agent(
    id="classifier-triager",
    name="Triage",
    model=MODEL,
    db=agent_db,
    instructions=TRIAGE_INSTRUCTIONS,
)

paper_specialist = Agent(
    id="classifier-paper",
    name="Paper Specialist",
    model=MODEL,
    db=agent_db,
    tools=[ArxivTools()],
    instructions=PAPER_INSTRUCTIONS,
    markdown=True,
)

document_specialist = Agent(
    id="classifier-document",
    name="Document Specialist",
    model=MODEL,
    db=agent_db,
    tools=_docling_tools(),
    instructions=DOCUMENT_INSTRUCTIONS,
    markdown=True,
)

video_specialist = Agent(
    id="classifier-video",
    name="Video Specialist",
    model=MODEL,
    db=agent_db,
    tools=[YouTubeTools()],
    instructions=VIDEO_INSTRUCTIONS,
    markdown=True,
)

article_specialist = Agent(
    id="classifier-article",
    name="Web Specialist",
    model=MODEL,
    db=agent_db,
    tools=[WebsiteTools(), DuckDuckGoTools()],
    instructions=ARTICLE_INSTRUCTIONS,
    markdown=True,
)

topic_specialist = Agent(
    id="classifier-topic",
    name="Encyclopedia Specialist",
    model=MODEL,
    db=agent_db,
    tools=[WikipediaTools(), DuckDuckGoTools()],
    instructions=TOPIC_INSTRUCTIONS,
    markdown=True,
)

deep_analyst = Agent(
    id="classifier-deep",
    name="Deep Analyst",
    model=MODEL,
    db=agent_db,
    instructions=DEEP_ANALYSIS_INSTRUCTIONS,
    markdown=True,
)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------
paper_step = Step(name="Paper", agent=paper_specialist)
document_step = Step(name="Document", agent=document_specialist)
video_step = Step(name="Video", agent=video_specialist)
article_step = Step(name="Article", agent=article_specialist)
topic_step = Step(name="Topic", agent=topic_specialist)


# ---------------------------------------------------------------------------
# Router selector — parse the triager's SOURCE_TYPE to pick a specialist
# ---------------------------------------------------------------------------
def route_to_specialist(step_input: StepInput) -> list[Step]:
    """Route to the correct specialist based on the triager's SOURCE_TYPE line."""
    content = str(step_input.previous_step_content or "").upper()
    if "SOURCE_TYPE: PAPER" in content:
        return [paper_step]
    if "SOURCE_TYPE: DOCUMENT" in content:
        return [document_step]
    if "SOURCE_TYPE: VIDEO" in content:
        return [video_step]
    if "SOURCE_TYPE: TOPIC" in content:
        return [topic_step]
    # Default to the web/article specialist for unrecognized or generic URLs
    return [article_step]


# ---------------------------------------------------------------------------
# Condition evaluator — run deep analysis for dense sources
# ---------------------------------------------------------------------------
def is_deep(step_input: StepInput) -> bool:
    """Check whether the triager flagged this source for a deep-analysis pass."""
    for output in (step_input.previous_step_outputs or {}).values():
        if "DEPTH: DEEP" in str(output.content or "").upper():
            return True
    return False


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------
classifier = Workflow(
    id="classifier",
    name="Classifier",
    description="Classifies an incoming source, routes it to the right real-tool specialist, and deep-dives dense ones.",
    steps=[
        Step(name="Classify", agent=triager),
        Router(
            name="Route to Specialist",
            selector=route_to_specialist,  # type: ignore[arg-type]
            choices=[paper_step, document_step, video_step, article_step, topic_step],
        ),
        Condition(
            name="Deep Analysis Check",
            evaluator=is_deep,
            steps=[Step(name="Deep Analysis", agent=deep_analyst)],
        ),
    ],
)
