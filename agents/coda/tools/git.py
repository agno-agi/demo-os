"""Git tools for repository exploration and worktree management."""

import re
import subprocess
from pathlib import Path

from agno.tools import Toolkit
from agno.utils.log import logger


class GitTools(Toolkit):
    """Toolkit for git operations on repositories within a base directory.

    Provides read-only exploration (log, diff, blame, show), repository
    discovery (list_repos, repo_summary), and worktree lifecycle management
    (create, list, remove).

    All paths are validated to stay within the configured base directory.
    """

    def __init__(self, base_dir: str = "/repos", read_only: bool = False):
        tools: list = [
            self.git_log,
            self.git_diff,
            self.git_blame,
            self.git_show,
            self.git_fetch,
            self.git_branches,
            self.list_repos,
            self.repo_summary,
            self.get_github_remote,
            self.list_worktrees,
        ]
        if not read_only:
            tools += [self.create_worktree, self.remove_worktree, self.git_push]
        super().__init__(name="git_tools", tools=tools)
        self.base_dir = Path(base_dir)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, repo: str) -> Path:
        """Resolve a repo name to an absolute path under base_dir.

        Raises:
            ValueError: If the resolved path is outside base_dir or does not exist.
        """
        resolved = (self.base_dir / repo).resolve()
        if not resolved.is_relative_to(self.base_dir.resolve()):
            raise ValueError(f"Path escapes base directory: {repo}")
        if not resolved.is_dir():
            raise ValueError(f"Repository not found: {resolved}")
        return resolved

    def _run(self, cmd: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        """Run a git command with standard settings."""
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def git_log(
        self,
        repo: str,
        path: str = "",
        n: int = 20,
        since: str = "",
    ) -> str:
        """Show recent git commits for a repository.

        Args:
            repo: Repository name (directory under the base repos path).
            path: Optional file or directory path to filter commits.
            n: Maximum number of commits to return (default 20).
            since: Optional date filter, e.g. '2024-01-01' or '2 weeks ago'.

        Returns:
            One-line-per-commit log output, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            cmd = ["git", "log", "--oneline", "-n", str(n)]
            if since:
                cmd.append(f"--since={since}")
            if path:
                cmd += ["--", path]
            result = self._run(cmd, cwd=repo_path)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            return result.stdout.strip() or "(no commits)"
        except Exception as e:
            logger.warning(f"git_log failed: {e}")
            return f"Error: {e}"

    def git_diff(
        self,
        repo: str,
        ref1: str,
        ref2: str = "HEAD",
        path: str = "",
        stat: bool = False,
    ) -> str:
        """Show the diff between two git refs.

        Supports branch ranges like ``main..feature-branch`` in *ref1*
        (leave *ref2* empty) or as separate args.

        Args:
            repo: Repository name.
            ref1: Starting ref (commit, branch, or tag). Can also be a range
                like ``main..feature-branch``.
            ref2: Ending ref (default HEAD). Ignored when *ref1* contains ``..``.
            path: Optional file path to restrict the diff.
            stat: If True, return a ``--stat`` summary instead of the full diff.
                Useful for getting a file-level overview of large changes.

        Returns:
            Diff output (truncated to 20 000 chars), or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            # Allow ref1 to carry a full range (e.g. "main..feature")
            if ".." in ref1:
                cmd = ["git", "diff", ref1]
            else:
                cmd = ["git", "diff", f"{ref1}..{ref2}"]
            if stat:
                cmd.append("--stat")
            if path:
                cmd += ["--", path]
            result = self._run(cmd, cwd=repo_path)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            output = result.stdout.strip()
            if len(output) > 20000:
                return output[:20000] + "\n\n... [truncated — diff exceeds 20 000 chars]"
            return output or "(no diff)"
        except Exception as e:
            logger.warning(f"git_diff failed: {e}")
            return f"Error: {e}"

    def git_blame(
        self,
        repo: str,
        path: str,
        start_line: int = 1,
        end_line: int = 50,
    ) -> str:
        """Show line-by-line blame (authorship) for a file.

        Args:
            repo: Repository name.
            path: File path relative to the repository root.
            start_line: First line to blame (default 1).
            end_line: Last line to blame (default 50).

        Returns:
            Blame output for the requested line range, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            cmd = ["git", "blame", "-L", f"{start_line},{end_line}", path]
            result = self._run(cmd, cwd=repo_path)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            return result.stdout.strip() or "(no blame output)"
        except Exception as e:
            logger.warning(f"git_blame failed: {e}")
            return f"Error: {e}"

    def git_show(self, repo: str, ref: str) -> str:
        """Show commit metadata and a stat summary for a ref.

        Uses --stat to keep output concise (file-level summary, no full diff).

        Args:
            repo: Repository name.
            ref: Commit hash, branch, or tag to inspect.

        Returns:
            Commit info with diffstat summary, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            cmd = ["git", "show", ref, "--stat"]
            result = self._run(cmd, cwd=repo_path)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            return result.stdout.strip() or "(no output)"
        except Exception as e:
            logger.warning(f"git_show failed: {e}")
            return f"Error: {e}"

    def git_fetch(self, repo: str) -> str:
        """Fetch the latest refs from origin.

        Downloads all remote branches and tags without modifying the working
        tree. This is a read-only network operation — safe to call at any time.

        Args:
            repo: Repository name.

        Returns:
            Success confirmation or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            result = self._run(["git", "fetch", "origin"], cwd=repo_path, timeout=120)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            return "Fetched latest refs from origin."
        except Exception as e:
            logger.warning(f"git_fetch failed: {e}")
            return f"Error: {e}"

    def git_branches(self, repo: str, remote: bool = True) -> str:
        """List branches in a repository.

        Args:
            repo: Repository name.
            remote: If True (default), include remote tracking branches
                (``origin/*``). If False, list only local branches.

        Returns:
            Formatted branch list, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            cmd = ["git", "branch"]
            if remote:
                cmd.append("-a")
            result = self._run(cmd, cwd=repo_path)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            return result.stdout.strip() or "(no branches)"
        except Exception as e:
            logger.warning(f"git_branches failed: {e}")
            return f"Error: {e}"

    def list_repos(self) -> str:
        """List all git repositories in the base directory.

        For each repository found, shows the directory name, current branch,
        and the subject line of the most recent commit.

        Returns:
            Formatted list of repositories, or an error message.
        """
        try:
            if not self.base_dir.is_dir():
                return f"Error: base directory does not exist: {self.base_dir}"
            repos: list[str] = []
            for entry in sorted(self.base_dir.iterdir()):
                if entry.is_dir() and (entry / ".git").exists():
                    name = entry.name
                    # Current branch
                    branch_result = self._run(
                        ["git", "branch", "--show-current"],
                        cwd=entry,
                    )
                    branch = branch_result.stdout.strip() or "(detached)"
                    # Last commit subject
                    log_result = self._run(
                        ["git", "log", "--oneline", "-1"],
                        cwd=entry,
                    )
                    last_commit = log_result.stdout.strip() or "(no commits)"
                    repos.append(f"  {name}  ({branch})  {last_commit}")
            if not repos:
                return "(no git repositories found)"
            return "Repositories:\n" + "\n".join(repos)
        except Exception as e:
            logger.warning(f"list_repos failed: {e}")
            return f"Error: {e}"

    def repo_summary(self, repo: str) -> str:
        """Get an overview of a repository: file listing, recent commits, branch, and README.

        Args:
            repo: Repository name.

        Returns:
            Multi-section summary string, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            sections: list[str] = []

            # Current branch
            branch_result = self._run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
            )
            branch = branch_result.stdout.strip() or "(detached)"
            sections.append(f"Branch: {branch}")

            # Top-level listing
            entries = sorted(p.name for p in repo_path.iterdir() if not p.name.startswith("."))
            sections.append("Files:\n  " + "\n  ".join(entries) if entries else "Files: (empty)")

            # Recent commits
            log_result = self._run(
                ["git", "log", "--oneline", "-5"],
                cwd=repo_path,
            )
            log_output = log_result.stdout.strip()
            sections.append(f"Recent commits:\n{log_output}" if log_output else "Recent commits: (none)")

            # README detection
            readme_names = ["README.md", "README.rst", "README.txt", "README"]
            found_readme = next((r for r in readme_names if (repo_path / r).is_file()), None)
            if found_readme:
                sections.append(f"README: {found_readme}")
            else:
                sections.append("README: (not found)")

            return "\n\n".join(sections)
        except Exception as e:
            logger.warning(f"repo_summary failed: {e}")
            return f"Error: {e}"

    def get_github_remote(self, repo: str) -> str:
        """Get the GitHub owner/repo identifier for a repository.

        Parses the origin remote URL into ``owner/repo`` format
        (e.g. ``"agno-agi/agno"``).  Works with both HTTPS and SSH URLs.

        Args:
            repo: Repository name (directory under the base repos path).

        Returns:
            The ``owner/repo`` string, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            result = self._run(["git", "remote", "get-url", "origin"], cwd=repo_path)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            url = result.stdout.strip()
            # HTTPS: https://github.com/owner/repo.git
            # SSH:   git@github.com:owner/repo.git
            match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
            if not match:
                return f"Error: could not parse GitHub owner/repo from remote URL: {url}"
            return match.group(1)
        except Exception as e:
            logger.warning(f"get_github_remote failed: {e}")
            return f"Error: {e}"

    def git_push(self, repo: str, branch: str = "") -> str:
        """Push a branch to origin.

        Only allows pushing ``coda/*`` branches. Force-push is never used.

        Args:
            repo: Repository name.
            branch: Branch name to push. If empty, pushes the current branch.

        Returns:
            Success confirmation or an error message.
        """
        try:
            repo_path = self._repo_path(repo)

            # Resolve branch name if not provided
            if not branch:
                result = self._run(["git", "branch", "--show-current"], cwd=repo_path)
                branch = result.stdout.strip()
                if not branch:
                    return "Error: could not determine current branch (detached HEAD?)"

            # Safety: only push coda/* branches
            if not branch.startswith("coda/"):
                return f"Error: refusing to push branch '{branch}'. Only coda/* branches can be pushed."

            result = self._run(
                ["git", "push", "-u", "origin", branch],
                cwd=repo_path,
                timeout=120,
            )
            if result.returncode != 0:
                return f"Error pushing: {result.stderr.strip()}"
            return f"Pushed {branch} to origin."
        except Exception as e:
            logger.warning(f"git_push failed: {e}")
            return f"Error: {e}"

    def create_worktree(
        self,
        repo: str,
        task_name: str,
        base_ref: str = "HEAD",
    ) -> str:
        """Create a git worktree for an isolated task.

        Fetches the latest refs from origin, then creates a new worktree at
        worktrees/<task_name> on a new branch named coda/<task_name>.

        Args:
            repo: Repository name.
            task_name: Short identifier for the task (used in path and branch name).
            base_ref: Ref to branch from (default HEAD).

        Returns:
            The absolute path to the new worktree, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)

            # Fetch latest refs (best-effort — may fail if no remote configured)
            fetch_result = self._run(["git", "fetch", "origin"], cwd=repo_path, timeout=120)
            if fetch_result.returncode != 0:
                logger.warning(f"git fetch origin warning: {fetch_result.stderr.strip()}")

            worktree_path = repo_path / "worktrees" / task_name
            branch_name = f"coda/{task_name}"
            cmd = [
                "git",
                "worktree",
                "add",
                str(worktree_path),
                "-b",
                branch_name,
                base_ref,
            ]
            result = self._run(cmd, cwd=repo_path)
            if result.returncode != 0:
                return f"Error creating worktree: {result.stderr.strip()}"
            return f"Worktree created: {worktree_path}"
        except Exception as e:
            logger.warning(f"create_worktree failed: {e}")
            return f"Error: {e}"

    def list_worktrees(self, repo: str) -> str:
        """List all worktrees for a repository.

        Args:
            repo: Repository name.

        Returns:
            Output of git worktree list, or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            result = self._run(["git", "worktree", "list"], cwd=repo_path)
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            return result.stdout.strip() or "(no worktrees)"
        except Exception as e:
            logger.warning(f"list_worktrees failed: {e}")
            return f"Error: {e}"

    def remove_worktree(self, repo: str, task_name: str) -> str:
        """Remove a worktree and clean up its branch.

        Removes worktrees/<task_name> and deletes the local branch
        coda/<task_name>.

        Args:
            repo: Repository name.
            task_name: Task identifier matching the worktree to remove.

        Returns:
            Success confirmation or an error message.
        """
        try:
            repo_path = self._repo_path(repo)
            worktree_rel = f"worktrees/{task_name}"
            branch_name = f"coda/{task_name}"

            # Remove the worktree
            wt_result = self._run(
                ["git", "worktree", "remove", worktree_rel],
                cwd=repo_path,
            )
            if wt_result.returncode != 0:
                return f"Error removing worktree: {wt_result.stderr.strip()}"

            # Clean up the local branch
            br_result = self._run(
                ["git", "branch", "-d", branch_name],
                cwd=repo_path,
            )
            if br_result.returncode != 0:
                return f"Worktree removed, but branch cleanup failed: {br_result.stderr.strip()}"

            return f"Removed worktree '{worktree_rel}' and branch '{branch_name}'."
        except Exception as e:
            logger.warning(f"remove_worktree failed: {e}")
            return f"Error: {e}"
