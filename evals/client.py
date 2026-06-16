"""
AgentOS HTTP Client
===================

Central HTTP client for all eval interactions. Every test goes through this.

Usage:
    from evals.client import AgentOSClient

    client = AgentOSClient(base_url="http://localhost:8000")
    result = client.run_agent("docs", "What is Agno?")
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class RunResult:
    status_code: int
    content: str
    raw_json: dict
    duration: float
    error: str | None = None
    tool_calls: list[str] = field(default_factory=list)


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
            # Parse SSE stream — extract content from terminal event
            raw = {}
            content = ""
            content_chunks: list[str] = []
            tool_calls: list[str] = []
            for line in r.text.split("\n"):
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    evt = data.get("event", "")
                    if evt in ("RunCompleted", "TeamRunCompleted", "WorkflowCompleted"):
                        raw = data
                        content = data.get("content", "")
                        # Don't break on RunCompleted inside workflows —
                        # keep going to find WorkflowCompleted
                        if evt != "RunCompleted":
                            break
                    elif evt in ("RunContent", "TeamRunContent") and data.get("content"):
                        content_chunks.append(data["content"])
                    elif evt in ("ToolCallStarted", "TeamToolCallStarted"):
                        tool = data.get("tool") or (data.get("tools", [{}])[0] if data.get("tools") else {})
                        tool_name = tool.get("tool_name", "") if isinstance(tool, dict) else ""
                        if tool_name:
                            tool_calls.append(tool_name)
                    elif evt in ("RunPaused", "TeamRunPaused"):
                        raw = data
                        # Include tool names and args in content for testability
                        parts = [data.get("content", "")]
                        for tool in data.get("tools", []):
                            tool_name = tool.get("tool_name", "")
                            parts.append(tool_name)
                            parts.append(json.dumps(tool.get("tool_args", {})))
                            if tool_name:
                                tool_calls.append(tool_name)
                        content = " ".join(parts)
                        break
            # If no RunCompleted/RunPaused content, assemble from chunks
            if not content and content_chunks:
                content = "".join(content_chunks)
            return RunResult(
                status_code=r.status_code,
                content=content,
                raw_json=raw,
                duration=duration,
                tool_calls=tool_calls,
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
