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

import re

from agno.agent import Agent
from agno.tools.arxiv import ArxivTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.website import WebsiteTools
from agno.tools.wikipedia import WikipediaTools
from agno.tools.youtube import YouTubeTools
from agno.workflow import Condition, Router, Step, Workflow
from agno.workflow.types import StepInput, StepOutput

from app.settings import MODEL
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
    """Build DoclingTools lazily so the workflow imports even if docling isn't installed.

    Uses full-page OCR (easyocr): some real-world PDFs (e.g. the Berkshire letter) have
    a text layer docling-parse can't extract — they only parse when each page is OCR'd as
    an image (pdf_force_full_page_ocr=True). This mirrors Agno's docling OCR cookbook.
    """
    try:
        from agno.tools.docling import DoclingTools

        return [
            DoclingTools(
                pdf_enable_ocr=True,
                pdf_ocr_engine="easyocr",
                pdf_ocr_lang=["pt", "en"],
                pdf_force_full_page_ocr=True,
                pdf_enable_table_structure=True,
                pdf_enable_picture_description=False,
                pdf_document_timeout=120.0,
            )
        ]
    except ImportError:
        return []


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
triager = Agent(
    id="classifier-triager",
    name="Triage",
    model=MODEL,
    instructions=TRIAGE_INSTRUCTIONS,
)

paper_specialist = Agent(
    id="classifier-paper",
    name="Paper Specialist",
    model=MODEL,
    tools=[ArxivTools()],
    instructions=PAPER_INSTRUCTIONS,
    markdown=True,
)

document_specialist = Agent(
    id="classifier-document",
    name="Document Specialist",
    model=MODEL,
    tools=_docling_tools(),
    instructions=DOCUMENT_INSTRUCTIONS,
    markdown=True,
)

video_specialist = Agent(
    id="classifier-video",
    name="Video Specialist",
    model=MODEL,
    tools=[YouTubeTools()],
    instructions=VIDEO_INSTRUCTIONS,
    markdown=True,
)

article_specialist = Agent(
    id="classifier-article",
    name="Web Specialist",
    model=MODEL,
    tools=[WebsiteTools(), DuckDuckGoTools()],
    instructions=ARTICLE_INSTRUCTIONS,
    markdown=True,
)

topic_specialist = Agent(
    id="classifier-topic",
    name="Encyclopedia Specialist",
    model=MODEL,
    tools=[WikipediaTools(), DuckDuckGoTools()],
    instructions=TOPIC_INSTRUCTIONS,
    markdown=True,
)

deep_analyst = Agent(
    id="classifier-deep",
    name="Deep Analyst",
    model=MODEL,
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
# Router selector — read the source-type word from the triager's sentence
# ---------------------------------------------------------------------------
def _has_word(text: str, word: str) -> bool:
    """Whole-word, case-insensitive match (so 'paper' doesn't match 'newspaper')."""
    return re.search(rf"\b{word}\b", text, re.IGNORECASE) is not None


def route_to_specialist(step_input: StepInput) -> list[Step]:
    """Route to the correct specialist based on the source-type word the triager used.

    The triager replies in plain language but always includes exactly one of
    paper/document/video/article/topic. Checked most-specific first; article is the default.
    """
    content = str(step_input.previous_step_content or "")
    if _has_word(content, "paper"):
        return [paper_step]
    if _has_word(content, "document"):
        return [document_step]
    if _has_word(content, "video"):
        return [video_step]
    if _has_word(content, "topic"):
        return [topic_step]
    # Default to the web/article specialist for unrecognized or generic URLs
    return [article_step]


# ---------------------------------------------------------------------------
# Condition evaluator — run deep analysis for dense sources
# ---------------------------------------------------------------------------
def is_deep(step_input: StepInput) -> bool:
    """Check whether the triager called for a deep-analysis pass."""
    for output in (step_input.previous_step_outputs or {}).values():
        if _has_word(str(output.content or ""), "deep"):
            return True
    return False


# ---------------------------------------------------------------------------
# Finalize — collapse Router/Condition container outputs into one clean answer
# ---------------------------------------------------------------------------
def _deepest_content(output) -> str:
    """Walk a container StepOutput down to its innermost real content."""
    cur = output
    while getattr(cur, "steps", None):
        cur = cur.steps[-1]
    return str(getattr(cur, "content", "") or "")


def finalize(step_input: StepInput) -> StepOutput:
    """Surface the specialist (or deep-analysis) answer as the single final output.

    A workflow that ends on a Router/Condition surfaces the specialist's body twice —
    once nested in the container's step trace and once as the run's final answer. Ending
    on this plain step makes the final answer a single distinct output, so the UI shows
    one clean result instead of duplicated runs.
    """
    outputs = step_input.previous_step_outputs or {}
    cond = outputs.get("Deep Analysis Check")
    if cond and getattr(cond, "steps", None):  # deep analysis ran
        return StepOutput(content=_deepest_content(cond))
    router = outputs.get("Route to Specialist")
    if router and getattr(router, "steps", None):  # a specialist ran
        return StepOutput(content=_deepest_content(router))
    return StepOutput(content=str(step_input.previous_step_content or "").strip() or "No result produced.")


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
        Step(name="Finalize", executor=finalize),
    ],
    store_executor_outputs=False,
)
