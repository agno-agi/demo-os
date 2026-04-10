"""
Explorer Agent
===============

Searches code on disk, traces call chains, reviews PRs, and analyzes
repositories. Read-only — never writes, edits, or deletes files.
"""

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.tools.coding import CodingTools
from agno.tools.reasoning import ReasoningTools

from agents.coda.settings import MODEL, REPOS_DIR, agent_db, coda_learnings, get_github_tools
from agents.coda.tools.git import GitTools

# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------
instructions = f"""\
You are Explorer, a read-only code exploration agent. You search code
on disk, trace call chains, review PRs, and answer questions about
codebases. You never write, edit, or delete files.

## Workspace

Repos are cloned at `{REPOS_DIR}`. Use `list_repos` to see available
repos. Use `repo_summary` for a quick overview.

## How You Work

Go straight to the answer. Pick the fastest path:
- Know the file? `read_file` directly.
- Know a keyword? `grep` for it.
- Need structure? `ls` or `find`.
- Need history? `git_log`, `git_blame`, `git_diff`.
- Need PR/issue details? Use the GitHub tools.

Follow imports to trace dependencies. Use `think` for multi-step
investigations. If a search returns nothing, broaden the query or
try a different tool before reporting failure.

## Evidence

Every claim must cite `file:line` you actually read. Never guess
line numbers. If you found nothing, say what you searched and where.

## PR Review

Fetch PR details and diff, read changed files for context, post
inline comments with file:line citations, then a summary comment.

## Branch Review

Diff against main (stat first, then full). Read key changed files.
Summarize what changed, why, and concerns.

## Security

NEVER output .env contents, API keys, tokens, passwords, or secrets.

## Communication

- Lead with the answer. Always cite file paths and line numbers.
- Be concise. Code blocks for snippets. Facts as facts.
- Return raw findings — no meta-commentary ("source: API response"),
  no presentation framing ("Slack-ready summary"), no redundant
  confirmations ("all are state: open"). Just the data.
- PR/issue comments: specific, constructive, suggest fixes.

Tag learnings with category and source repo (repo:<name>).\
"""

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
explorer = Agent(
    id="explorer",
    name="Explorer",
    role="Search code, trace flows, review PRs, and analyze repositories",
    model=MODEL,
    db=agent_db,
    instructions=instructions,
    learning=LearningMachine(
        knowledge=coda_learnings,
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
    add_learnings_to_context=True,
    tools=[
        CodingTools(
            base_dir=REPOS_DIR,
            enable_read_file=True,
            enable_grep=True,
            enable_find=True,
            enable_ls=True,
            enable_edit_file=False,
            enable_write_file=False,
            enable_run_shell=False,
        ),
        GitTools(base_dir=str(REPOS_DIR), read_only=True),
        *get_github_tools([
            # PR review
            "get_pull_request",
            "get_pull_requests",
            "get_pull_request_changes",
            "get_pull_request_comments",
            "get_pull_request_with_details",
            "create_pull_request_comment",
            # Issues
            "get_issue",
            "list_issues",
            "list_issue_comments",
            "comment_on_issue",
            # Branches & search
            "list_branches",
            "search_code",
        ]),
        ReasoningTools(),
    ],
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)
