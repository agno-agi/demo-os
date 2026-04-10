"""
Syncer Agent
============

Commits and pushes context/ changes to GitHub after file-creating
workflows complete. Writes descriptive commit messages based on
what changed. Also handles pulling remote changes.

This is how Pal's knowledge base stays durable and portable — no
volumes needed. Git is the persistence layer.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIResponses

from agents.pal.settings import agent_db
from agents.pal.tools import build_syncer_tools

SYNCER_INSTRUCTIONS = """\
You are the Syncer, responsible for pushing context/ changes to GitHub.

## Your Job
When called, commit and push all pending changes in context/ to GitHub.

1. Use `sync_status` to see what changed
2. Write a short, descriptive commit message based on the changes:
   - "Ingest 2 articles on RAG techniques"
   - "Compile context-engineering and vector-search concepts"
   - "Weekly review for 2026-04-03"
   - "Lint report: 3 warnings, 2 suggestions"
   - "Daily briefing for 2026-04-03"
3. Use `sync_push` with that message
4. Confirm the result

## Commit Message Rules
- Start with a verb: Ingest, Compile, Add, Update, Lint, Draft
- Keep it under 72 characters
- Be specific about what changed, not generic ("sync changes" is bad)
- If multiple things changed, summarize the most important one

## When to Pull
Use `sync_pull` when asked to refresh from remote, or when another
agent reports a conflict.

## What You Do NOT Do
- Do not modify files — you only commit and push what others created
- Do not answer user questions
- Do not interact with email, calendar, or Slack\
"""

syncer = Agent(
    id="syncer",
    name="Syncer",
    role="Commits and pushes context/ changes to GitHub",
    model=OpenAIResponses(id="gpt-5.4"),
    db=agent_db,
    instructions=SYNCER_INSTRUCTIONS,
    tools=build_syncer_tools(),
    add_datetime_to_context=True,
    markdown=True,
)
