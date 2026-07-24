"""
Improvement Data Collector
==========================

Runs an entity via HTTP, captures the response and Docker logs,
reads the instruction file, and prints everything to stdout.
Claude Code reads this output and decides what to change.

Usage (called BY Claude Code):
    python -m evals improve --entity knowledge
    python -m evals improve --entity dash
    python -m evals improve --failures
    python -m evals improve --entity knowledge --json
"""

from __future__ import annotations

import json as json_mod
from datetime import UTC
from pathlib import Path

from evals.client import AgentOSClient
from evals.docker import DockerLogCapture
from evals.registry import ENTITIES
from evals.smoke import run_smoke_tests


def _read_file(path: str) -> str:
    """Read a file, returning its contents or an error message."""
    abs_path = Path(path).resolve()
    try:
        return abs_path.read_text()
    except FileNotFoundError:
        return f"[FILE NOT FOUND: {abs_path}]"


def _get_smoke_results_for_entity(client: AgentOSClient, entity_id: str) -> list[dict]:
    """Run smoke tests for a specific entity and return results."""
    return run_smoke_tests(client, entity=entity_id)


def collect_improvement_data(
    client: AgentOSClient,
    entity_id: str,
    project_root: str = ".",
    docker_container: str = "agno-demo-api",
) -> str:
    """Collect all improvement data for a single entity. Returns formatted text."""
    entity = ENTITIES.get(entity_id)
    if not entity:
        return f"Unknown entity: {entity_id}"

    entity_type = entity.type
    docker = DockerLogCapture(container=docker_container, project_root=project_root)

    # Run smoke tests for this entity
    smoke_results = _get_smoke_results_for_entity(client, entity_id)

    # Find a failing test to get the prompt, or use the first test
    failing = [r for r in smoke_results if r["status"] == "FAIL"]
    test_prompt = failing[0].get("prompt", "") if failing else None

    # If no specific failing prompt, use the smoke test prompt
    if not test_prompt:
        from evals.cases.smoke import all_smoke_tests

        entity_tests = [t for t in all_smoke_tests() if t.entity_id == entity_id and t.group != "security"]
        test_prompt = entity_tests[0].prompt if entity_tests else f"Hello, test for {entity_id}"

    # Run the entity and capture Docker logs
    mark = docker.mark()
    run_result = client.run(entity_type, entity_id, test_prompt)
    logs = docker.capture_since(mark)

    # Read instruction and agent definition files
    instruction_rel = entity.instruction_file
    definition_rel = entity.definition_file
    instruction_path = str(Path(project_root, instruction_rel).resolve()) if instruction_rel else ""
    definition_path = str(Path(project_root, definition_rel).resolve()) if definition_rel else ""

    # Format smoke results
    smoke_lines = []
    for r in smoke_results:
        line = f'{r["id"]}  {r["entity_id"]}  "{r.get("name", "")}"  {r["status"]}'
        if r.get("reason"):
            line += f"  {r['reason']}"
        smoke_lines.append(line)

    # Build output
    from datetime import datetime

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    sections = [
        "=== IMPROVEMENT DATA ===",
        f"ENTITY_TYPE: {entity_type}",
        f"ENTITY_ID: {entity_id}",
        f"TIMESTAMP: {timestamp}",
        "",
        "=== SMOKE RESULTS ===",
        *smoke_lines,
        "",
        "=== RUN DETAIL ===",
        f"PROMPT: {test_prompt}",
        f"STATUS: {run_result.status_code}",
        f"DURATION: {run_result.duration}s",
        "",
        "--- RESPONSE ---",
        run_result.content or "[empty response]",
        "",
        "--- DOCKER LOGS ---",
        logs.stdout or "[no logs captured]",
    ]

    if logs.stderr:
        sections.extend(["", "--- DOCKER STDERR ---", logs.stderr])

    if instruction_path:
        sections.extend(
            [
                "",
                "=== INSTRUCTION FILE ===",
                f"PATH: {instruction_path}",
                "--- CONTENTS ---",
                _read_file(instruction_path),
            ]
        )

    if definition_path:
        sections.extend(
            [
                "",
                "=== AGENT DEFINITION ===",
                f"PATH: {definition_path}",
                "--- CONTENTS ---",
                _read_file(definition_path),
            ]
        )

    sections.append("\n=== END ===")

    return "\n".join(sections)


def collect_improvement_json(
    client: AgentOSClient,
    entity_id: str,
    project_root: str = ".",
    docker_container: str = "agno-demo-api",
) -> dict:
    """Collect improvement data as structured dict (for --json mode)."""
    entity = ENTITIES.get(entity_id)
    if not entity:
        return {"error": f"Unknown entity: {entity_id}"}

    docker = DockerLogCapture(container=docker_container, project_root=project_root)
    smoke_results = _get_smoke_results_for_entity(client, entity_id)

    failing = [r for r in smoke_results if r["status"] == "FAIL"]
    test_prompt = failing[0].get("prompt", "") if failing else None
    if not test_prompt:
        from evals.cases.smoke import all_smoke_tests

        entity_tests = [t for t in all_smoke_tests() if t.entity_id == entity_id and t.group != "security"]
        test_prompt = entity_tests[0].prompt if entity_tests else f"Hello, test for {entity_id}"

    mark = docker.mark()
    run_result = client.run(entity.type, entity_id, test_prompt)
    logs = docker.capture_since(mark)

    instruction_path = str(Path(project_root, entity.instruction_file).resolve())
    definition_path = str(Path(project_root, entity.definition_file).resolve())

    return {
        "entity_id": entity_id,
        "entity_type": entity.type,
        "smoke_results": smoke_results,
        "failing_tests": failing,
        "run": {
            "prompt": test_prompt,
            "response": run_result.content or "",
            "status_code": run_result.status_code,
            "duration": run_result.duration,
            "tool_calls": run_result.tool_calls,
        },
        "docker_logs": {"stdout": logs.stdout, "stderr": logs.stderr},
        "files": {
            "instructions": {"path": instruction_path, "content": _read_file(instruction_path)},
            "definition": {"path": definition_path, "content": _read_file(definition_path)},
        },
    }


def run_improve(
    client: AgentOSClient,
    entity_id: str | None = None,
    failures_only: bool = False,
    project_root: str = ".",
    docker_container: str = "agno-demo-api",
    output_json: bool = False,
) -> None:
    """Main entry point for the improvement data collector."""
    collector = collect_improvement_json if output_json else collect_improvement_data

    if failures_only:
        # Run full smoke suite, collect failures
        print("Running smoke tests to find failures...\n")
        results = run_smoke_tests(client)
        failed_ids = list({r["entity_id"] for r in results if r["status"] == "FAIL"})

        if not failed_ids:
            print("\nAll smoke tests passed — nothing to improve.")
            return

        print(f"\nFailing entities: {', '.join(sorted(failed_ids))}\n")
        print("=" * 60)

        for eid in sorted(failed_ids):
            output = collector(client, eid, project_root, docker_container)
            if output_json:
                print(json_mod.dumps(output, indent=2))
            else:
                print(output)
            print("\n" + "=" * 60 + "\n")
    elif entity_id:
        output = collector(client, entity_id, project_root, docker_container)
        if output_json:
            print(json_mod.dumps(output, indent=2))
        else:
            print(output)
    else:
        print("Usage: python -m evals improve --entity <id> | --failures")
