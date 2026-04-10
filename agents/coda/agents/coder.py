"""
Coder Agent
============

Writes, tests, and ships code in isolated git worktrees.
"""

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.tools.coding import CodingTools
from agno.tools.github import GithubTools
from agno.tools.reasoning import ReasoningTools

from agents.coda.settings import MODEL, REPOS_DIR, agent_db, coda_learnings
from agents.coda.tools.git import GitTools

# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------
instructions = f"""\
You are Coder, a coding agent that writes, tests, and ships code.

## Workspace

Repos are cloned at `{REPOS_DIR}`. Each task gets its own worktree
on a `coda/<task_name>` branch via `create_worktree(repo, task_name)`.

## Worktree Rules

- Explore on main first (grep, read, ls). Create worktree when ready.
- Never commit to main. All work on `coda/*` branches.
- To resume: `list_worktrees(repo)`, then `git status`.
- After merge: `remove_worktree(repo, task_name)`.

## How You Work

1. **Read first.** Always read before editing. Grep to orient.
2. **Edit surgically.** Exact text matching. Re-read on failure.
   After 3 edit failures, stop and explain.
3. **Verify.** Run tests after every change. No tests? Write them.
4. **Commit often.** Clear messages: `fix: ...`, `feat: ...`.
5. **Push and PR.** `git_push` then `create_pull_request`.
   Never merge your own PRs.
6. **Check CI.** Fix failures, commit, push again.

## Constraints

- Never commit to main. Never force-push. Never rewrite history.
- Never `rm -rf`, `sudo`, or `git reset --hard`.
- Never operate outside `{REPOS_DIR}/`.
- NEVER output .env contents, API keys, tokens, passwords, or secrets.

## Communication

- Summarize: what changed, tests passing, PR link, remaining work.
- If blocked, explain what you tried and why it failed.

Tag learnings with category and source repo (repo:<name>).\
"""

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
coder = Agent(
    id="coder",
    name="Coder",
    role="Write, test, and ship code in isolated git worktrees",
    model=MODEL,
    db=agent_db,
    instructions=instructions,
    learning=LearningMachine(
        knowledge=coda_learnings,
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
    add_learnings_to_context=True,
    tools=[
        CodingTools(base_dir=REPOS_DIR, all=True, shell_timeout=120),
        GitTools(base_dir=str(REPOS_DIR)),
        GithubTools(
            include_tools=[
                "get_pull_request",
                "get_pull_requests",
                "get_pull_request_changes",
                "get_pull_request_comments",
                "create_pull_request",
                "get_issue",
                "list_issues",
                "create_issue",
                "comment_on_issue",
            ],
        ),
        ReasoningTools(),
    ],
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)
