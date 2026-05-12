"""
Registry for the Demo AgentOS.

Provides shared tools, models, and database connections for AgentOS.

Models and tools are gated on their provider's API key (or optional
package availability) so the registry stays importable regardless
of which keys are configured.
"""

from os import getenv

from agno.models.openai import OpenAIResponses
from agno.registry import Registry

from app.settings import MODEL, agent_db, get_parallel_tools


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
    from agno.tools.yfinance import YFinanceTools
    from agno.tools.youtube import YouTubeTools

    tools: list = [
        *get_parallel_tools(),
        # Data & utility
        CalculatorTools(),
        FileTools(),
        FileGenerationTools(),
        YFinanceTools(),
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
# Registry
# ---------------------------------------------------------------------------
registry = Registry(
    tools=_get_tools(),
    models=_get_models(),
    dbs=[agent_db],
)
