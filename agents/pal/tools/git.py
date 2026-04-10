"""Git sync tools — commit and push context/ to GitHub, pull remote changes."""

import subprocess
from pathlib import Path

from agno.tools import tool

from agents.pal.config import PAL_CONTEXT_DIR


def run_git(args: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    """Run a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd or PAL_CONTEXT_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Git command timed out"
    except (OSError, ValueError) as e:
        return False, str(e)


def init_context_repo(repo_url: str) -> str:
    """Initialize context/ as a git repo synced with GitHub.

    Called at startup. If context/ is already a git repo, pulls latest.
    If not, initializes and connects to remote.

    Args:
        repo_url: GitHub repo URL (e.g. https://github.com/user/pal-context.git)

    Returns:
        Status message.
    """
    context_dir = PAL_CONTEXT_DIR

    # Check if already a git repo
    git_dir = context_dir / ".git"
    if git_dir.exists():
        # Already initialized — pull latest
        ok, out = run_git(["pull", "--rebase", "--autostash"])
        if ok:
            return f"Context repo pulled: {out or 'up to date'}"
        return f"Context pull failed: {out}"

    # Initialize new repo
    run_git(["init"], cwd=context_dir)
    run_git(["remote", "add", "origin", repo_url], cwd=context_dir)

    # Try to pull existing content
    ok, out = run_git(["fetch", "origin"])
    if ok:
        # Check if remote has a main branch
        ok_branch, _ = run_git(["rev-parse", "--verify", "origin/main"])
        if ok_branch:
            run_git(["checkout", "-B", "main", "--track", "origin/main"])
            return "Context repo initialized and pulled from remote."

    # No remote content yet — initial commit
    run_git(["checkout", "-b", "main"])
    run_git(["add", "-A"])
    run_git(["commit", "-m", "Initial context sync"])
    ok, out = run_git(["push", "-u", "origin", "main"])
    if ok:
        return "Context repo initialized and pushed to remote."
    return f"Context repo initialized locally. Push failed: {out}"


def create_sync_tools():
    """Create git sync tools for the Syncer agent.

    Returns:
        List of tool functions.
    """

    @tool
    def sync_push(message: str) -> str:
        """Commit and push all context/ changes to GitHub.

        Call this after creating or modifying files in context/ (raw/, wiki/,
        meetings/, projects/). Writes a descriptive commit message.

        Args:
            message: A short, descriptive commit message summarizing what changed
                (e.g. "Add 3 wiki articles on RAG techniques",
                "Compile rag-survey into concept articles",
                "Weekly review for 2026-04-03").

        Returns:
            Status message with commit details.
        """
        # Check for changes
        ok, status = run_git(["status", "--porcelain"])
        if ok and not status:
            return "Nothing to sync — no changes in context/."

        # Stage all changes
        run_git(["add", "-A"])

        # Commit
        ok, out = run_git(["commit", "-m", message])
        if not ok:
            return f"Commit failed: {out}"

        # Push
        ok, out = run_git(["push"])
        if ok:
            return f"Synced to GitHub: {message}"
        return f"Committed locally but push failed: {out}"

    @tool
    def sync_pull() -> str:
        """Pull latest context/ changes from GitHub.

        Call this to get changes made locally or by other instances.
        Uses rebase + autostash to handle any local uncommitted work.

        Returns:
            Status message.
        """
        ok, out = run_git(["pull", "--rebase", "--autostash"])
        if ok:
            return f"Pulled latest: {out or 'already up to date'}"
        return f"Pull failed: {out}"

    @tool
    def sync_status() -> str:
        """Check the sync status — uncommitted changes, ahead/behind remote.

        Returns:
            Git status summary.
        """
        parts = []

        ok, status = run_git(["status", "--porcelain"])
        if ok:
            if status:
                lines = status.strip().split("\n")
                parts.append(f"{len(lines)} uncommitted change(s):\n{status}")
            else:
                parts.append("No uncommitted changes.")

        ok, log = run_git(["log", "--oneline", "-5"])
        if ok and log:
            parts.append(f"Recent commits:\n{log}")

        return "\n\n".join(parts) if parts else "Unable to read git status."

    return [sync_push, sync_pull, sync_status]
