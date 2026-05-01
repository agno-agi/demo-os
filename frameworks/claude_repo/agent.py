"""
Repo Explainer (Claude Agent SDK)
=================================

A Claude-powered agent that explains any public GitHub repo. Uses Claude's
native WebSearch + WebFetch tools to read the repo's README, find the entry
point, and summarize architecture without local filesystem access.

Demonstrates: serving a Claude Agent SDK agent through AgentOS.
"""

from agno.agents.claude import ClaudeAgent

from app.settings import agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are Repo Explainer, a Claude Agent SDK agent that explains public GitHub repos.

When the user gives you a repo (owner/name or full URL):
1. Use WebFetch on the repo's README to understand purpose and features.
2. Use WebFetch / WebSearch to inspect the file tree, the entry point, and key modules.
3. Produce a concise summary covering: what the repo does, the main entry point,
   the architecture in 3-5 bullets, and notable dependencies.

Always cite the URLs you read. Keep the summary under 300 words unless asked
for a deep dive. If the user asks about a private or non-existent repo, say so.
"""

claude_repo = ClaudeAgent(
    id="claude-repo",
    name="Repo Explainer (Claude SDK)",
    description="Explains public GitHub repos using Claude's native web tools.",
    db=agent_db,
    system_prompt=SYSTEM_PROMPT,
    model="claude-sonnet-4-5",
    allowed_tools=["WebSearch", "WebFetch"],
    max_turns=10,
)
