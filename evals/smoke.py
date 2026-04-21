"""
Smoke Test Runner
=================

Pattern-matching tests — no LLM judge, no cost, fast.

Usage:
    from evals.smoke import run_smoke_tests
    from evals.client import AgentOSClient

    client = AgentOSClient()
    results = run_smoke_tests(client, group="agents", verbose=True)
"""

from __future__ import annotations

import os
import re

from evals.cases.smoke import SmokeTest, all_smoke_tests
from evals.client import AgentOSClient, RunResult


def _check_requires(requires: list[str]) -> tuple[bool, str]:
    """Check if required env vars are present.

    Supports negation: "!VAR" means the test runs only when VAR is absent.
    Returns (should_run, skip_reason).
    """
    for var in requires:
        if var.startswith("!"):
            # Negated — run only when key is MISSING
            real_var = var[1:]
            if os.environ.get(real_var):
                return False, f"{real_var} is set (test requires it absent)"
        else:
            if not os.environ.get(var):
                return False, f"requires {var}"
    return True, ""


def _check_assertions(test: SmokeTest, result: RunResult) -> tuple[bool, str]:
    """Run all assertions against the response. Returns (passed, failure_reason)."""
    content = result.content

    # response_contains (case-insensitive substring)
    for substring in test.response_contains:
        if substring.lower() not in content.lower():
            return False, f"missing: {substring}"

    # response_not_contains (case-insensitive substring)
    for substring in test.response_not_contains:
        if substring.lower() in content.lower():
            return False, f"found forbidden: {substring}"

    # response_matches (regex)
    for pattern in test.response_matches:
        if not re.search(pattern, content):
            return False, f"no match: {pattern}"

    return True, ""


def run_smoke_tests(
    client: AgentOSClient,
    group: str | None = None,
    entity: str | None = None,
    verbose: bool = False,
) -> list[dict]:
    """Run smoke tests filtered by group and/or entity.

    Returns a list of result dicts with keys:
        id, name, entity_id, status (PASS|FAIL|SKIP|ERROR), duration, reason
    """
    tests = all_smoke_tests()

    if group:
        tests = [t for t in tests if t.group == group]
    if entity:
        tests = [t for t in tests if t.entity_id == entity]

    if not tests:
        print(f"No smoke tests found (group={group}, entity={entity})")
        return []

    print(f"\n=== smoke ({len(tests)} tests) ===\n")

    results: list[dict] = []
    for i, test in enumerate(tests, 1):
        print(f"  [{i}/{len(tests)}] {test.id} {test.entity_id}: {test.prompt[:60]}")

        # Check env var requirements
        should_run, skip_reason = _check_requires(test.requires)
        if not should_run:
            result = {
                "id": test.id,
                "name": test.name,
                "entity_type": test.entity_type,
                "entity_id": test.entity_id,
                "group": test.group,
                "prompt": test.prompt,
                "status": "SKIP",
                "duration": 0.0,
                "reason": skip_reason,
            }
            results.append(result)
            print(f"         SKIP — {skip_reason}")
            continue

        # Run the agent/team/workflow
        run_result = client.run(
            test.entity_type,
            test.entity_id,
            test.prompt,
            timeout=test.timeout,
        )

        if run_result.error:
            result = {
                "id": test.id,
                "name": test.name,
                "entity_type": test.entity_type,
                "entity_id": test.entity_id,
                "group": test.group,
                "prompt": test.prompt,
                "status": "ERROR",
                "duration": run_result.duration,
                "reason": run_result.error,
            }
            results.append(result)
            print(f"         ERROR ({run_result.duration}s) — {run_result.error[:80]}")
            if verbose:
                print(f"         Response: {run_result.content[:200]}")
            continue

        # Check assertions
        passed, failure_reason = _check_assertions(test, run_result)

        # Check latency
        if passed and test.max_duration and run_result.duration > test.max_duration:
            passed = False
            failure_reason = f"too slow: {run_result.duration}s > {test.max_duration}s"

        status = "PASS" if passed else "FAIL"
        result = {
            "id": test.id,
            "name": test.name,
            "entity_type": test.entity_type,
            "entity_id": test.entity_id,
            "group": test.group,
            "prompt": test.prompt,
            "status": status,
            "duration": run_result.duration,
        }
        if not passed:
            result["reason"] = failure_reason
        results.append(result)

        if passed:
            print(f"         PASS ({run_result.duration}s)")
        else:
            print(f"         FAIL ({run_result.duration}s) — {failure_reason}")

        if verbose:
            print(f"         Response: {run_result.content[:200]}")

    # Summary
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    skipped_count = sum(1 for r in results if r["status"] == "SKIP")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    total_duration = round(sum(r["duration"] for r in results), 1)

    print(f"\n{'=' * 50}")
    print(
        f"Results: {passed_count} passed, {failed_count} failed, "
        f"{skipped_count} skipped, {error_count} errors ({total_duration}s)"
    )
    print(f"{'=' * 50}")

    return results
