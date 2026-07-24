"""
Docker Log Capture
==================

Captures Docker container logs during agent runs for the improvement loop.
Uses timestamp-based slicing to isolate logs from a specific run.

Usage:
    from evals.docker import DockerLogCapture

    docker = DockerLogCapture()
    mark = docker.mark()
    # ... run agent via HTTP ...
    logs = docker.capture_since(mark)
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class DockerLogs:
    stdout: str
    stderr: str
    container: str


class DockerLogCapture:
    """Capture Docker Compose logs for a specific time window."""

    def __init__(
        self,
        container: str = "agno-demo-api",
        project_root: str = ".",
    ):
        self.container = container
        self.project_root = project_root

    def mark(self) -> str:
        """Capture current timestamp as anchor for log slicing."""
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def capture_since(self, since: str) -> DockerLogs:
        """Get container logs since the given timestamp."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "logs",
                    self.container,
                    "--since",
                    since,
                    "--no-color",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
                check=False,
            )
            return DockerLogs(
                stdout=result.stdout,
                stderr=result.stderr,
                container=self.container,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return DockerLogs(
                stdout="",
                stderr=f"Failed to capture logs: {e}",
                container=self.container,
            )
