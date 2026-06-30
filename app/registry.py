"""
Registry for the Demo AgentOS.

Provides the shared building blocks AgentOS exposes to Studio: tools, models,
databases, knowledge bases, memory/session-summary managers, and the raw
workflow functions used by the Studio workflow builder.

Each bucket maps to a Studio surface:
- ``tools`` / ``models`` / ``dbs`` / ``knowledge`` / ``memory_managers`` /
  ``session_summary_managers`` are shown on ``/studio/registry``.
- ``functions`` are raw workflow callables (executors, selectors, evaluators,
  loop end-conditions, output-review gates) used by the workflow builder's
  component picker — NOT agent tools.

Models, tools, and managers are gated on their provider's API key (or optional
package availability) so the registry stays importable regardless of which
keys are configured.
"""

from os import getenv
from typing import List

from agno.models.openai import OpenAIResponses
from agno.registry import Registry
from agno.session.summary import SessionSummaryManager
from agno.workflow.types import StepInput, StepOutput

from agents.dash.settings import dash_knowledge, dash_learnings
from app.settings import MODEL, agent_db, get_parallel_tools
from teams.coach.team import coach_learnings


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
def _get_models() -> list:
    """Build the model list, gating optional providers on their API key."""
    models: list = [
        # OpenAI — always available (OPENAI_API_KEY is required)
        MODEL,
        OpenAIResponses(id="gpt-5.4-mini"),
    ]

    if getenv("ANTHROPIC_API_KEY"):
        from agno.models.anthropic import Claude

        models.extend(
            [
                Claude(id="claude-opus-4-7"),
                Claude(id="claude-opus-4-6"),
                Claude(id="claude-sonnet-4-6"),
                Claude(id="claude-haiku-4-5-20251001"),
            ]
        )

    if getenv("GOOGLE_API_KEY"):
        from agno.models.google import Gemini

        models.extend(
            [
                Gemini(id="gemini-3.1-pro-preview"),
                Gemini(id="gemini-3-flash-preview"),
                Gemini(id="gemini-3.1-flash-lite-preview"),
            ]
        )

    return models


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def _get_tools() -> list:
    """Build the tool list, gating optional tools on API keys or packages."""
    from agno.tools.arxiv import ArxivTools
    from agno.tools.calculator import CalculatorTools
    from agno.tools.coding import CodingTools
    from agno.tools.file import FileTools
    from agno.tools.file_generation import FileGenerationTools
    from agno.tools.hackernews import HackerNewsTools
    from agno.tools.openai import OpenAITools
    from agno.tools.pubmed import PubmedTools
    from agno.tools.reasoning import ReasoningTools
    from agno.tools.youtube import YouTubeTools

    tools: list = [
        *get_parallel_tools(),
        # Data & utility
        CalculatorTools(),
        FileTools(),
        FileGenerationTools(),
        # Code & reasoning
        CodingTools(),
        ReasoningTools(add_instructions=True),
        # Media — OPENAI_API_KEY is required, so always available
        OpenAITools(image_model="gpt-image-1.5-2025-12-16"),
        # Research — no API key needed
        ArxivTools(),
        HackerNewsTools(),
        PubmedTools(),
        YouTubeTools(),
    ]

    # Free search — needs ddgs package
    try:
        from agno.tools.duckduckgo import DuckDuckGoTools

        tools.append(DuckDuckGoTools())
    except ImportError:
        pass

    # Knowledge — needs wikipedia package
    try:
        from agno.tools.wikipedia import WikipediaTools

        tools.append(WikipediaTools())
    except ImportError:
        pass

    # --- Env-gated tools ---------------------------------------------------

    if getenv("ELEVEN_LABS_API_KEY"):
        from agno.tools.eleven_labs import ElevenLabsTools

        tools.append(ElevenLabsTools())

    if getenv("FAL_KEY"):
        from agno.tools.fal import FalTools

        tools.append(FalTools(api_key=getenv("FAL_KEY")))

    if getenv("GOOGLE_API_KEY"):
        from agno.tools.nano_banana import NanoBananaTools

        tools.append(NanoBananaTools())

    if getenv("EXA_API_KEY"):
        from agno.tools.exa import ExaTools

        tools.append(ExaTools())

    return tools


# ---------------------------------------------------------------------------
# Workflow functions
# ---------------------------------------------------------------------------
# Raw callables for the Studio workflow builder. These are NOT agent tools —
# they are the plain functions that drive workflow control flow: step
# executors, router selectors, condition evaluators, loop end-conditions, and
# output-review gates. Where practical they mirror the live demo workflows.
def preprocess_input_executor(step_input: StepInput) -> StepOutput:
    """Step executor: normalize and trim raw user input for downstream steps."""
    raw = step_input.input or ""
    cleaned = " ".join(str(raw).split()).strip()
    return StepOutput(content=f"Normalized input ({len(cleaned)} chars): {cleaned}")


def route_by_category(step_input: StepInput) -> str:
    """Router selector: pick a branch from the prior step's ``CATEGORY:`` line."""
    content = str(step_input.previous_step_content or "").upper()
    if "CATEGORY: BILLING" in content:
        return "Billing"
    if "CATEGORY: ACCOUNT" in content:
        return "Account"
    return "Technical"


def is_high_severity(step_input: StepInput) -> bool:
    """Condition evaluator: escalate when the classifier reports HIGH/CRITICAL."""
    for output in (step_input.previous_step_outputs or {}).values():
        content = str(output.content or "").upper()
        if "SEVERITY: HIGH" in content or "SEVERITY: CRITICAL" in content:
            return True
    return False


def needs_fact_checking(step_input: StepInput) -> bool:
    """Condition evaluator: fact-check only when content shows numeric/source claims."""
    content = (step_input.previous_step_content or "").lower()
    indicators = ("study", "report", "percent", "%", "million", "billion", "according to")
    return any(token in content for token in indicators)


def approved_end_condition(outputs: List[StepOutput]) -> bool:
    """Loop end_condition: stop once the last output ends with ``APPROVED``."""
    if not outputs:
        return False
    last_output = str(outputs[-1].content or "").strip()
    if not last_output:
        return False
    last_line = last_output.split("\n")[-1]
    return last_line.strip(" \t*_`.!?,:;").upper() == "APPROVED"


def substantial_content_end_condition(outputs: List[StepOutput]) -> bool:
    """Loop end_condition: stop once any iteration produces substantial content."""
    if not outputs:
        return False
    return any(o.content and len(str(o.content)) > 200 for o in outputs)


def needs_human_review(output: StepOutput) -> bool:
    """Output review gate (``requires_output_review``): flag thin/uncertain output."""
    content = str(output.content or "")
    return len(content) < 50 or "uncertain" in content.lower()


# ---------------------------------------------------------------------------
# Memory & session-summary managers
# ---------------------------------------------------------------------------
def _get_memory_managers() -> list:
    """Build differently-configured MemoryManagers, gating Claude on its key."""
    from agno.memory.manager import MemoryManager

    # Default manager — always available (uses the shared OpenAI MODEL).
    managers: list = [
        MemoryManager(
            model=MODEL,
            db=agent_db,
            additional_instructions=(
                'Capture durable user preferences and facts. Refer to the user as "the User" rather than by name.'
            ),
        ),
    ]

    if getenv("ANTHROPIC_API_KEY"):
        from agno.models.anthropic import Claude

        managers.append(
            MemoryManager(
                model=Claude(id="claude-sonnet-4-6"),
                db=agent_db,
                memory_capture_instructions=(
                    "Capture code snippets and information about the code. "
                    "Skip ephemeral details from the current code."
                ),
                additional_instructions="Be concise. Prefer one-line memories.",
            )
        )

    return managers


def _get_session_summary_managers() -> list:
    """Build concise + verbose SessionSummaryManagers, gating Claude on its key."""
    managers: list = [
        SessionSummaryManager(
            model=MODEL,
            session_summary_prompt=(
                "Summarize the conversation in 3-5 bullet points focused on "
                "decisions, open questions, and any follow-ups required."
            ),
            last_n_runs=10,
        ),
    ]

    if getenv("ANTHROPIC_API_KEY"):
        from agno.models.anthropic import Claude

        managers.append(
            SessionSummaryManager(
                model=Claude(id="claude-sonnet-4-6"),
                session_summary_prompt=(
                    "Produce a detailed narrative summary covering context, key exchanges, outcomes, and next steps."
                ),
                conversation_limit=50,
            )
        )

    return managers


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
registry = Registry(
    tools=_get_tools(),
    models=_get_models(),
    dbs=[agent_db],
    knowledge=[
        dash_knowledge,
        dash_learnings,
        coach_learnings,
    ],
    functions=[
        preprocess_input_executor,
        route_by_category,
        is_high_severity,
        needs_fact_checking,
        approved_end_condition,
        substantial_content_end_condition,
        needs_human_review,
    ],
    memory_managers=_get_memory_managers(),
    session_summary_managers=_get_session_summary_managers(),
)
