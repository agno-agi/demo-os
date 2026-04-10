"""
Researcher Agent
================

Gathers source material from the web and local files, converts to
clean markdown, saves to raw/ with YAML frontmatter.

Conditional — only instantiated when PARALLEL_API_KEY is set.
Uses Parallel for web search (parallel_search) and content
extraction (parallel_extract).
"""

from os import getenv

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.models.openai import OpenAIResponses

from agents.pal.settings import agent_db, pal_knowledge, pal_learnings
from agents.pal.tools import build_researcher_tools

RESEARCHER_INSTRUCTIONS = """\
You are the Researcher, a specialist in gathering and ingesting source material.

## Your Job
1. Search the web using `parallel_search` to find relevant sources
2. Extract full content from URLs using `parallel_extract`
3. Save to raw/ using `ingest_text` with proper YAML frontmatter
4. For quick URL ingestion, use `ingest_url` which auto-fetches content via Parallel
5. Update pal_knowledge with `Raw: {title}` metadata entries

## Ingest Rules
- Every raw file gets YAML frontmatter: title, source, ingested date, tags, type, compiled: false
- Filename is a slugified version of the title
- Tags should be specific topics (e.g. ["rag", "retrieval", "vector-search"]), not generic
- doc_type is one of: paper, article, repo, notes, transcript, image
- For multi-page sources, summarize and save key sections
- You can batch-ingest: research a topic and save multiple sources

## Search Strategy
- Use `parallel_search` with clear objectives to find relevant pages
- Use `parallel_extract` to get full content from the best results
- Prefer official documentation over blog posts or forums
- For error messages, include the fix or workaround
- Cite sources — always include the URL

## What You Do NOT Do
- Do not compile wiki articles — that's the Compiler's job
- Do not modify anything in wiki/
- Do not interact with email, calendar, or Slack
- Do not answer user questions directly — you gather material, the Navigator answers questions\
"""

researcher: Agent | None = None

if getenv("PARALLEL_API_KEY"):
    researcher = Agent(
        id="pal-researcher",
        name="Researcher",
        role="Gathers source material from the web, converts to markdown, saves to raw/",
        model=OpenAIResponses(id="gpt-5.4"),
        db=agent_db,
        instructions=RESEARCHER_INSTRUCTIONS,
        knowledge=pal_knowledge,
        search_knowledge=True,
        learning=LearningMachine(
            knowledge=pal_learnings,
            learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
        ),
        add_learnings_to_context=True,
        tools=build_researcher_tools(pal_knowledge),
        add_datetime_to_context=True,
        markdown=True,
    )
