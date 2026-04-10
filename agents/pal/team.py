"""
Pal — Personal Knowledge Agent
================================

A personal agent that learns how you work and builds a compounding
knowledge base from everything you feed it.

Pal is a team of specialists coordinated by a leader:
- Navigator:  routes queries, reads wiki, handles email/calendar/SQL/files
- Researcher: gathers sources from the web, ingests to raw/ (conditional)
- Compiler:   reads raw/, compiles structured wiki articles
- Linter:     health checks on the wiki, finds gaps
- Syncer:     commits and pushes context/ changes to GitHub (conditional)

Test:
    python -m agents.pal
"""

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.models.openai import OpenAIResponses
from agno.team import Team, TeamMode

from agents.pal.agents import compiler, linter, navigator, researcher, syncer
from agents.pal.config import GIT_SYNC_ENABLED, SLACK_TOKEN
from agents.pal.settings import agent_db, pal_learnings

# ---------------------------------------------------------------------------
# Team Leader Tools (Slack — leader-only)
# ---------------------------------------------------------------------------
leader_tools: list = []
if SLACK_TOKEN:
    from agno.tools.slack import SlackTools

    leader_tools.append(
        SlackTools(
            enable_send_message=True,
            enable_list_channels=True,
            enable_send_message_thread=False,
            enable_get_channel_history=False,
            enable_upload_file=False,
            enable_download_file=False,
        )
    )

# ---------------------------------------------------------------------------
# Team Instructions
# ---------------------------------------------------------------------------
_researcher_row = (
    '| "Ingest this", "save this article", research a topic | **Researcher** '
    '| "ingest https://...", "research RAG techniques", "save this paper" |\n'
)

LEADER_INSTRUCTIONS = f"""\
You are Pal, a personal knowledge agent that learns how the user works.

You lead a team of specialists. Route requests to the right agent:

| Request Type | Agent | Examples |
|-------------|-------|---------|
| Knowledge queries, briefings, email, calendar, SQL, files | **Navigator** | "what do I know about X?", "check my email", "what's on my calendar?" |
{_researcher_row if researcher else ""}\
| "Compile the wiki", "update the knowledge base" | **Compiler** | "compile new sources", after new ingests |
| "Check wiki health", "find gaps", "lint the wiki" | **Linter** | "lint the wiki", "what's missing?" |
| Greetings, thanks, "what can you do?" | Direct response | No delegation needed |

**Default to Navigator** for anything not clearly {"research/" if researcher else ""}compile/lint.

## How You Work

1. **Respond directly** ONLY for greetings, thanks, and "what can you do?" — nothing else.
2. **Everything else MUST be delegated.** You don't have file tools, SQL tools, or wiki tools — only your specialists do. Never answer from knowledge search metadata alone. **Drafting content (emails, Slack messages, documents) MUST go to Navigator** so it can read the matching voice guide first.
3. **Your `update_user_memory` is ONLY for personal preferences** ("I prefer dark mode", "call me bestie", "I'm in EST"). Notes, meetings, people, projects, and anything with entities or facts goes to **Navigator** for SQL storage. When the user says "save a note", "remember this meeting", or "jot this down" — delegate to Navigator.
4. **Delegate briefly.** Pass the user's question with enough context. Don't over-specify.
5. **Synthesize.** Rewrite specialist output into a clean, concise response for the user.\
"""

RESEARCHER_DISABLED_INSTRUCTIONS = """

## Web Research — Enhanced Research Not Configured

For basic web search, the Navigator can use Exa (`web_search_exa`).
For full research workflows (search + extract + ingest), enable the Parallel integration by adding `PARALLEL_API_KEY` to your `.env` and restarting.\
"""

SYNC_CHAIN_INSTRUCTIONS = """

## Sync Chain

After any workflow that creates or modifies files in context/, **always delegate
to Syncer as the final step** to commit and push changes to GitHub. This ensures
the knowledge base is durable and available everywhere.

Chain examples:
- User ingests a URL → Researcher saves to raw/ → **Syncer pushes**
- Scheduled compile → Compiler writes wiki articles → **Syncer pushes**
- Scheduled lint → Linter writes lint report → **Syncer pushes**
- Navigator saves meeting notes or drafts a file → **Syncer pushes**
- Weekly review → Navigator writes to meetings/ → **Syncer pushes**

Do NOT skip the Syncer step. Every file change must be pushed.\
"""

SYNC_DISABLED_INSTRUCTIONS = """

## Git Sync — Not Configured

If the user asks about sync status, pushing, or pulling context, respond exactly:
> Git sync isn't set up yet. Context changes are only stored locally. Add `GITHUB_ACCESS_TOKEN` and `PAL_REPO_URL` to your `.env` and restart to enable git-backed persistence.

Do not delegate sync questions to Navigator.\
"""

SLACK_LEADER_INSTRUCTIONS = """

## Slack

When posting to Slack (scheduled tasks, user requests), use your SlackTools directly.\
"""

SLACK_DISABLED_LEADER_INSTRUCTIONS = """

## Slack — Not Configured

If the user asks to post to Slack, respond exactly:
> Slack isn't set up yet. Follow the setup guide in `docs/SLACK_CONNECT.md` to connect your workspace.

Do not attempt any Slack tool calls.\
"""

# Assemble instructions
instructions = LEADER_INSTRUCTIONS
if SLACK_TOKEN:
    instructions += SLACK_LEADER_INSTRUCTIONS
else:
    instructions += SLACK_DISABLED_LEADER_INSTRUCTIONS
if not researcher:
    instructions += RESEARCHER_DISABLED_INSTRUCTIONS
if GIT_SYNC_ENABLED:
    instructions += SYNC_CHAIN_INSTRUCTIONS
else:
    instructions += SYNC_DISABLED_INSTRUCTIONS

# ---------------------------------------------------------------------------
# Members — conditional on configuration
# ---------------------------------------------------------------------------
members: list[Agent | Team] = [m for m in [navigator, researcher, compiler, linter] if m is not None]
if GIT_SYNC_ENABLED:
    members.append(syncer)

# ---------------------------------------------------------------------------
# Create Team
# ---------------------------------------------------------------------------
pal = Team(
    id="pal",
    name="Pal",
    mode=TeamMode.coordinate,
    model=OpenAIResponses(id="gpt-5.4"),
    members=members,
    db=agent_db,
    instructions=instructions,
    tools=leader_tools,
    learning=LearningMachine(
        knowledge=pal_learnings,
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
    add_learnings_to_context=True,
    enable_agentic_memory=True,
    search_past_sessions=True,
    num_past_sessions_to_search=10,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Run Team
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        # Smoke 1: Direct response
        "Hey, what can you do?",
        # Smoke 2: Navigator — file retrieval
        "What do you know about my voice guidelines?",
        # Smoke 3: Navigator — Gmail fallback
        "Check my latest emails",
        # Smoke 4: Researcher — ingest (requires PARALLEL_API_KEY)
        "Ingest this article: https://example.com/article-on-rag",
        # Smoke 5: Navigator — knowledge query
        "What do I know about Project Atlas?",
        # Smoke 6: Navigator — capture
        "Save a note: Met with Sarah Chen from Acme Corp.",
        # Smoke 7: Compiler trigger
        "Compile any new sources into the wiki",
        # Smoke 8: Linter trigger
        "Run a health check on the wiki",
        # Smoke 9: Syncer — check status
        "What's the sync status?",
    ]
    for idx, prompt in enumerate(test_cases, start=1):
        print(f"\n--- Pal test case {idx}/{len(test_cases)} ---")
        print(f"Prompt: {prompt}")
        pal.print_response(prompt, stream=True)
