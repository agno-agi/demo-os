"""
AgentOS HTTP Client
===================

Central HTTP client for all eval interactions. Every test goes through this.

Usage:
    from evals.client import AgentOSClient

    client = AgentOSClient(base_url="http://localhost:8000")
    result = client.run_agent("knowledge", "What is Agno?")
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import httpx


@dataclass
class RunResult:
    status_code: int
    content: str
    raw_json: dict
    duration: float
    error: str | None = None


class AgentOSClient:
    """HTTP client for the AgentOS API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or os.environ.get("AGENTOS_URL") or "http://localhost:8000").rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def health_check(self) -> bool:
        """GET / — verify the server is up."""
        try:
            r = self.client.get(self.base_url)
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def run_agent(self, agent_id: str, message: str, **kwargs) -> RunResult:
        """POST /agents/{agent_id}/runs"""
        return self.run("agent", agent_id, message, **kwargs)

    def run_team(self, team_id: str, message: str, **kwargs) -> RunResult:
        """POST /teams/{team_id}/runs"""
        return self.run("team", team_id, message, **kwargs)

    def run_workflow(self, workflow_id: str, message: str, **kwargs) -> RunResult:
        """POST /workflows/{workflow_id}/runs"""
        return self.run("workflow", workflow_id, message, **kwargs)

    def run(
        self,
        entity_type: str,
        entity_id: str,
        message: str,
        timeout: float | None = None,
    ) -> RunResult:
        """Dispatch to the appropriate endpoint based on entity_type."""
        type_to_path = {
            "agent": "agents",
            "team": "teams",
            "workflow": "workflows",
        }
        path = type_to_path.get(entity_type)
        if not path:
            return RunResult(
                status_code=0,
                content="",
                raw_json={},
                duration=0.0,
                error=f"Unknown entity_type: {entity_type}",
            )

        url = f"{self.base_url}/{path}/{entity_id}/runs"
        payload = {"message": message}

        start = time.time()
        try:
            r = self.client.post(
                url,
                data=payload,
                timeout=timeout or self.timeout,
            )
            duration = round(time.time() - start, 2)
            if r.status_code != 200:
                return RunResult(
                    status_code=r.status_code,
                    content="",
                    raw_json={},
                    duration=duration,
                    error=f"HTTP {r.status_code}: {r.text[:200]}",
                )
            # Parse SSE stream — extract content from RunCompleted event
            raw = {}
            content = ""
            for line in r.text.split("\n"):
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[5:].strip())
                        if data.get("event") == "RunCompleted":
                            raw = data
                            content = data.get("content", "")
                            break
                    except json.JSONDecodeError:
                        continue
            return RunResult(
                status_code=r.status_code,
                content=content,
                raw_json=raw,
                duration=duration,
            )
        except httpx.TimeoutException:
            return RunResult(
                status_code=0,
                content="",
                raw_json={},
                duration=round(time.time() - start, 2),
                error=f"Timeout after {timeout or self.timeout}s",
            )
        except httpx.HTTPError as e:
            return RunResult(
                status_code=0,
                content="",
                raw_json={},
                duration=round(time.time() - start, 2),
                error=str(e),
            )
