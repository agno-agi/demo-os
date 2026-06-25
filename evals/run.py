"""
Eval Runner
===========

Runs Agno eval framework (AgentAsJudgeEval, AccuracyEval) against the
AgentOS HTTP API.

Each eval category lives in evals/cases/ and defines:
    - CASES: list of test inputs (strings or dicts)
    - CRITERIA: judge instructions (for AgentAsJudgeEval categories)
    - ENTITIES: list of (entity_type, entity_id) tuples to test against

The runner gets responses via HTTP, then hands them to Agno eval classes
for LLM-based judgment.

Usage:
    python -m evals
    python -m evals --category security
    python -m evals --verbose
"""

from __future__ import annotations

import importlib
import time
from typing import Callable, Literal

from agno.eval.accuracy import AccuracyEval
from agno.eval.agent_as_judge import AgentAsJudgeEval

from evals import CATEGORIES, JUDGE_MODEL
from evals.client import AgentOSClient

# ---------------------------------------------------------------------------
# Runners (one per Agno eval type)
# ---------------------------------------------------------------------------


def run_judge_cases(
    client: AgentOSClient,
    cases: list[str],
    criteria: str,
    entities: list[tuple[str, str]],
    category: str,
    scoring: Literal["numeric", "binary"],
    verbose: bool = False,
) -> list[dict]:
    """Run AgentAsJudgeEval (binary or numeric) across entities."""
    judge = AgentAsJudgeEval(
        name=f"AgentOS {category}",
        criteria=criteria,
        scoring_strategy=scoring,
        model=JUDGE_MODEL,
    )

    total = len(entities) * len(cases)
    results: list[dict] = []
    counter = 0

    for entity_type, entity_id in entities:
        for question in cases:
            counter += 1
            print(f"  [{counter}/{total}] {entity_id}: {question[:55]}...")
            start = time.time()
            try:
                run_result = client.run(entity_type, entity_id, question)
                duration = round(time.time() - start, 2)

                if run_result.error:
                    result: dict = {
                        "entity_id": entity_id,
                        "question": question,
                        "category": category,
                        "status": "ERROR",
                        "duration": duration,
                        "reason": run_result.error,
                    }
                else:
                    eval_result = judge.run(input=question, output=run_result.content)
                    passed = eval_result is not None and eval_result.pass_rate == 100.0
                    result = {
                        "entity_id": entity_id,
                        "question": question,
                        "category": category,
                        "status": "PASS" if passed else "FAIL",
                        "duration": duration,
                    }
                    if not passed and eval_result and eval_result.results:
                        result["reason"] = eval_result.results[0].reason
                    if verbose:
                        result["response_preview"] = run_result.content[:200]
            except Exception as e:
                result = {
                    "entity_id": entity_id,
                    "question": question,
                    "category": category,
                    "status": "ERROR",
                    "reason": str(e),
                    "duration": round(time.time() - start, 2),
                }
            results.append(result)
            _print_status(result, verbose)
    return results


def run_accuracy_cases(
    client: AgentOSClient,
    cases: list[dict],
    category: str,
    verbose: bool = False,
) -> list[dict]:
    """Run AccuracyEval cases (expected output comparison, scored 1-10)."""
    results: list[dict] = []

    for i, case in enumerate(cases, 1):
        entity_type = case["entity_type"]
        entity_id = case["entity_id"]
        question = case["input"]
        expected = case["expected_output"]
        guidelines = case.get("guidelines")

        print(f"  [{i}/{len(cases)}] {entity_id}: {question[:55]}...")
        start = time.time()
        try:
            run_result = client.run(entity_type, entity_id, question)
            duration = round(time.time() - start, 2)

            if run_result.error:
                result: dict = {
                    "entity_id": entity_id,
                    "question": question,
                    "category": category,
                    "status": "ERROR",
                    "duration": duration,
                    "reason": run_result.error,
                }
            else:
                eval_obj = AccuracyEval(
                    name=f"Accuracy: {question[:40]}",
                    input=question,
                    expected_output=expected,
                    model=JUDGE_MODEL,
                    additional_guidelines=guidelines,
                )
                eval_result = eval_obj.run_with_output(output=run_result.content)

                passed = eval_result is not None and eval_result.avg_score is not None and eval_result.avg_score >= 7.0
                result = {
                    "entity_id": entity_id,
                    "question": question,
                    "category": category,
                    "status": "PASS" if passed else "FAIL",
                    "duration": duration,
                }
                if eval_result and eval_result.results:
                    result["score"] = eval_result.results[0].score
                    if not passed:
                        result["reason"] = eval_result.results[0].reason
                if verbose:
                    result["response_preview"] = run_result.content[:200]
        except Exception as e:
            result = {
                "entity_id": entity_id,
                "question": question,
                "category": category,
                "status": "ERROR",
                "reason": str(e),
                "duration": round(time.time() - start, 2),
            }
        results.append(result)
        _print_status(result, verbose)
    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _print_status(result: dict, verbose: bool) -> None:
    icon = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR "}.get(result["status"], "??? ")
    score = f" (score: {result['score']})" if "score" in result else ""
    print(f"         {icon} ({result['duration']}s){score}")
    if verbose and result.get("reason"):
        print(f"         Reason: {result['reason']}")


# ---------------------------------------------------------------------------
# Runner dispatch
# ---------------------------------------------------------------------------

RUNNERS: dict[str, Callable[..., list[dict]]] = {
    "judge_binary": lambda client, mod, cat, v: run_judge_cases(
        client, mod.CASES, mod.CRITERIA, mod.ENTITIES, cat, "binary", v
    ),
    "judge_numeric": lambda client, mod, cat, v: run_judge_cases(
        client, mod.CASES, mod.CRITERIA, mod.ENTITIES, cat, "numeric", v
    ),
    "accuracy": lambda client, mod, cat, v: run_accuracy_cases(client, mod.CASES, cat, v),
}


def run_evals(
    client: AgentOSClient,
    category: str | None = None,
    verbose: bool = False,
) -> bool:
    """Run Agno eval categories via HTTP and display results.

    Returns True if all cases passed, False otherwise.
    """
    all_results: list[dict] = []
    total_start = time.time()

    for name, config in CATEGORIES.items():
        if category and name != category:
            continue

        module = importlib.import_module(config["module"])
        eval_type = config["type"]

        if eval_type in ("judge_binary", "judge_numeric"):
            case_count = len(module.ENTITIES) * len(module.CASES)
        else:
            case_count = len(module.CASES)

        print(f"\n--- {name} ({case_count} cases) ---\n")

        runner = RUNNERS[eval_type]
        all_results.extend(runner(client, module, name, verbose))

    if not all_results:
        print(f"No cases found for category: {category}")
        return False

    # Summary
    total_duration = round(time.time() - total_start, 2)
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    failed = sum(1 for r in all_results if r["status"] == "FAIL")
    errors = sum(1 for r in all_results if r["status"] == "ERROR")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {errors} errors ({total_duration}s)")
    print(f"{'=' * 50}\n")

    return failed + errors == 0
