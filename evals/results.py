"""
Result Persistence
==================

Write eval results to JSON, compare across runs, detect regressions.

Usage:
    from evals.results import save_results, load_latest, compare

    path = save_results(results, "smoke")
    prev = load_latest("smoke")
    regressions = compare(results, prev["results"])
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / ".results"


def save_results(results: list[dict], suite: str) -> Path:
    """Save results to timestamped JSON file. Returns the file path."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{suite}_{ts}.json"
    path.write_text(
        json.dumps(
            {
                "suite": suite,
                "timestamp": ts,
                "results": results,
                "summary": _summarize(results),
            },
            indent=2,
        )
    )
    return path


def load_latest(suite: str) -> dict | None:
    """Load the most recent result file for a suite. Returns None if no results exist."""
    if not RESULTS_DIR.exists():
        return None
    files = sorted(RESULTS_DIR.glob(f"{suite}_*.json"), reverse=True)
    if not files:
        return None
    return json.loads(files[0].read_text())


def compare(current: list[dict], previous: list[dict]) -> list[dict]:
    """Find regressions: tests that passed before but fail now."""
    prev_map: dict[tuple, dict] = {}
    for r in previous:
        key = _result_key(r)
        prev_map[key] = r

    regressions = []
    for r in current:
        key = _result_key(r)
        prev = prev_map.get(key)
        if prev and prev["status"] == "PASS" and r["status"] != "PASS":
            regressions.append({**r, "regression": True, "previous_status": "PASS"})
    return regressions


def print_comparison(current: list[dict], previous: list[dict]) -> None:
    """Print regression summary to stdout."""
    regressions = compare(current, previous)
    if not regressions:
        print("\nNo regressions detected.")
        return

    print(f"\n{'=' * 50}")
    print(f"REGRESSIONS: {len(regressions)} test(s) that passed before now fail")
    print(f"{'=' * 50}")
    for r in regressions:
        reason = r.get("reason", "")
        print(f"  {r.get('id', r.get('entity_id', '?'))}  PASS -> {r['status']}  {reason}")


def _result_key(r: dict) -> tuple:
    """Build a stable key for matching results across runs."""
    return (
        r.get("id") or r.get("entity_id", ""),
        r.get("question", r.get("prompt", "")),
    )


def _summarize(results: list[dict]) -> dict:
    return {
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
        "errors": sum(1 for r in results if r["status"] == "ERROR"),
        "skipped": sum(1 for r in results if r.get("status") == "SKIP"),
    }
