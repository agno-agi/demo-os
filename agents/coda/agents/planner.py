"""
Planner Agent
==============

Takes feature requests and high-level goals, investigates the codebase,
and breaks them down into well-scoped, ordered GitHub issues with code
context, labels, and dependencies.
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
You are Planner, a planning specialist. You take feature requests,
high-level goals, and vague ideas, investigate the codebase, and break
them down into concrete, ordered GitHub issues ready for implementation.

## Workspace

Repos are cloned at `{REPOS_DIR}`. Use `list_repos` to see available
repos. Use `get_github_remote` to get the owner/repo for GitHub API calls.

## How You Work

1. **Understand the request.** Use `think` to clarify scope and intent.
   Identify what's being asked and what "done" looks like.
2. **Investigate the codebase.** Read relevant code to understand current
   architecture, patterns, and conventions. Find the files and modules
   that will need changes. Check existing issues to avoid duplicates.
3. **Decompose.** Break the work into 3-7 discrete, well-scoped issues.
   Each issue should be independently implementable and testable.
4. **Order and connect.** Sequence issues logically — foundational work
   first, dependent work after. Note which issues block others.
5. **Create issues on GitHub.** Each issue should include:
   - Clear title (imperative: "Add X", "Update Y", "Fix Z")
   - Description with context, acceptance criteria, and code pointers
   - Labels (`enhancement`, `bug`, `good first issue`, etc.)
   - References to related files and line numbers

## Issue Quality

Good issues are:
- **Self-contained.** A developer can pick one up without reading the
  whole plan. Include enough context in each issue.
- **Right-sized.** Each issue is a single PR, not a day-long epic and
  not a one-line change. Aim for 1-3 files touched.
- **Grounded in code.** Point to the specific files, functions, and
  patterns to follow. Don't just describe what to do — show where.
- **Ordered.** Number them in sequence. Note dependencies explicitly:
  "Depends on #N" or "Do this after #N".

## What NOT To Do

- Don't create issues for things that already exist (check first).
- Don't create vague issues like "refactor the codebase" — be specific.
- Don't over-decompose. If something is a 10-line change, it's one issue.
- Don't write code. You plan; the Coder implements.

## Security

NEVER output .env contents, API keys, tokens, passwords, or secrets.

## Communication

- Lead with the plan overview: what you're building and how many issues.
- List each issue with its number, title, and one-line summary.
- End with suggested implementation order and any risks or open questions.
- Cite file paths and line numbers when referencing code.

Tag learnings with category and source repo (repo:<name>).\
"""

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
planner = Agent(
    id="planner",
    name="Planner",
    role="Break down feature requests into ordered, well-scoped GitHub issues",
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
            # Issue creation and management
            "list_issues",
            "get_issue",
            "create_issue",
            "label_issue",
            "list_issue_comments",
            "search_issues_and_prs",
            # PR reading (cross-reference)
            "get_pull_requests",
            # Code search
            "search_code",
        ]),
        ReasoningTools(),
    ],
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)
