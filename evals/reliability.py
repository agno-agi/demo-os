"""
Reliability Eval Runner
========================

Client-side tool call validation. Compares actual tool calls
(parsed from SSE stream) against expected tool names.

Usage:
    python -m evals reliability
    python -m evals reliability --entity voyager
"""

from __future__ import annotations

import time

from evals.cases.reliability import CASES
from evals.client import AgentOSClient, RunResult


def check_reliability(result: RunResult, expected_tools: list[str]) -> tuple[bool, str]:
    """Check if expected tools were called. Returns (passed, reason)."""
    actual = set(result.tool_calls)
    expected = set(expected_tools)
    missing = expected - actual
    if missing:
        return False, f"missing tool calls: {sorted(missing)} (actual: {sorted(actual)})"
    return True, ""


def run_reliability_tests(
    client: AgentOSClient,
    entity: str | None = None,
    verbose: bool = False,
) -> list[dict]:
    """Run reliability cases and report results."""
    cases = CASES
    if entity:
        cases = [c for c in cases if c["entity_id"] == entity]

    if not cases:
        print(f"No reliability cases found (entity={entity})")
        return []

    print(f"\n=== reliability ({len(cases)} cases) ===\n")

    results: list[dict] = []
    for i, case in enumerate(cases, 1):
        entity_type = case["entity_type"]
        entity_id = case["entity_id"]
        prompt = case["input"]
        expected_tools = case["expected_tools"]

        print(f"  [{i}/{len(cases)}] {entity_id}: {prompt[:55]}...")
        start = time.time()

        run_result = client.run(entity_type, entity_id, prompt)
        duration = round(time.time() - start, 2)

        if run_result.error:
            result: dict = {
                "entity_id": entity_id,
                "prompt": prompt,
                "status": "ERROR",
                "duration": duration,
                "reason": run_result.error,
            }
        else:
            passed, reason = check_reliability(run_result, expected_tools)
            result = {
                "entity_id": entity_id,
                "prompt": prompt,
                "expected_tools": expected_tools,
                "actual_tools": run_result.tool_calls,
                "status": "PASS" if passed else "FAIL",
                "duration": duration,
            }
            if not passed:
                result["reason"] = reason

        results.append(result)

        icon = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR "}.get(result["status"], "??? ")
        print(f"         {icon} ({duration}s)")
        if result.get("reason"):
            print(f"         Reason: {result['reason']}")
        if verbose:
            print(f"         Expected: {expected_tools}")
            print(f"         Actual:   {run_result.tool_calls}")

    # Summary
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    total_duration = round(sum(r["duration"] for r in results), 1)

    print(f"\n{'=' * 50}")
    print(f"Results: {passed_count} passed, {failed_count} failed, {error_count} errors ({total_duration}s)")
    print(f"{'=' * 50}")

    return results
