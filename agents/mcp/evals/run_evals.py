"""
Run evaluations against the MCP agent.

Usage:
    python -m agents.mcp.evals.run_evals
    python -m agents.mcp.evals.run_evals --category concepts
    python -m agents.mcp.evals.run_evals --verbose
    python -m agents.mcp.evals.run_evals --llm-grader
"""

import argparse
import time
from typing import TypedDict

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from agents.mcp.evals.test_cases import CATEGORIES, TEST_CASES, TestCase


class EvalResult(TypedDict, total=False):
    status: str
    question: str
    category: str
    missing: list[str] | None
    duration: float
    response: str | None
    error: str
    llm_grade: float | None
    llm_reasoning: str | None


console = Console()


def check_strings_in_response(response: str, expected: list[str]) -> list[str]:
    """Check which expected strings are missing from the response."""
    response_lower = response.lower()
    return [v for v in expected if v.lower() not in response_lower]


def run_evals(
    category: str | None = None,
    verbose: bool = False,
    llm_grader: bool = False,
):
    """
    Run evaluation suite.

    Args:
        category: Filter tests by category
        verbose: Show full responses on failure
        llm_grader: Use LLM to grade responses
    """
    from agents.mcp.agent import mcp_agent

    # Filter tests
    tests = TEST_CASES
    if category:
        tests = [tc for tc in tests if tc.category == category]

    if not tests:
        console.print(f"[red]No tests found for category: {category}[/red]")
        return

    mode_info = ["LLM grading"] if llm_grader else ["String matching"]

    console.print(
        Panel(
            f"[bold]Running {len(tests)} tests[/bold]\nMode: {', '.join(mode_info)}",
            style="blue",
        )
    )

    results: list[EvalResult] = []
    start = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Evaluating...", total=len(tests))

        for test_case in tests:
            progress.update(task, description=f"[cyan]{test_case.question[:40]}...[/cyan]")
            test_start = time.time()

            try:
                run_result = mcp_agent.run(test_case.question)
                response = run_result.content or ""
                duration = time.time() - test_start

                eval_result = evaluate_response(
                    test_case=test_case,
                    response=response,
                    llm_grader=llm_grader,
                )

                results.append(
                    {
                        "status": eval_result["status"],
                        "question": test_case.question,
                        "category": test_case.category,
                        "missing": eval_result.get("missing"),
                        "duration": duration,
                        "response": response if verbose else None,
                        "llm_grade": eval_result.get("llm_grade"),
                        "llm_reasoning": eval_result.get("llm_reasoning"),
                    }
                )

            except Exception as e:
                duration = time.time() - test_start
                results.append(
                    {
                        "status": "ERROR",
                        "question": test_case.question,
                        "category": test_case.category,
                        "missing": None,
                        "duration": duration,
                        "error": str(e),
                        "response": None,
                    }
                )

            progress.advance(task)

    total_duration = time.time() - start

    display_results(results, verbose, llm_grader)
    display_summary(results, total_duration, category)


def evaluate_response(
    test_case: TestCase,
    response: str,
    llm_grader: bool = False,
) -> dict:
    """Evaluate an agent response using configured methods."""
    result: dict = {}

    missing = check_strings_in_response(response, test_case.expected_strings)
    result["missing"] = missing if missing else None
    string_pass = len(missing) == 0

    llm_pass: bool | None = None
    if llm_grader:
        try:
            from agents.mcp.evals.grader import grade_response

            grade = grade_response(
                question=test_case.question,
                response=response,
                expected_values=test_case.expected_strings,
            )
            result["llm_grade"] = grade.score
            result["llm_reasoning"] = grade.reasoning
            llm_pass = grade.passed
        except Exception as e:
            result["llm_grade"] = None
            result["llm_reasoning"] = f"Error: {e}"

    if llm_grader and llm_pass is not None:
        result["status"] = "PASS" if llm_pass else "FAIL"
    else:
        result["status"] = "PASS" if string_pass else "FAIL"

    return result


def display_results(
    results: list[EvalResult],
    verbose: bool,
    llm_grader: bool,
):
    """Display results table."""
    table = Table(title="Results", show_lines=True)
    table.add_column("Status", style="bold", width=6)
    table.add_column("Category", style="dim", width=16)
    table.add_column("Question", width=45)
    table.add_column("Time", justify="right", width=6)
    table.add_column("Notes", width=35)

    for r in results:
        if r["status"] == "PASS":
            status = Text("PASS", style="green")
            notes = ""
            if llm_grader and r.get("llm_grade") is not None:
                notes = f"LLM: {r['llm_grade']:.1f}"
        elif r["status"] == "FAIL":
            status = Text("FAIL", style="red")
            llm_reasoning = r.get("llm_reasoning")
            missing = r.get("missing")
            if llm_grader and llm_reasoning:
                notes = llm_reasoning[:35]
            elif missing:
                notes = f"Missing: {', '.join(missing[:2])}"
            else:
                notes = ""
        else:
            status = Text("ERR", style="yellow")
            notes = (r.get("error") or "")[:35]

        table.add_row(
            status,
            r["category"],
            r["question"][:43] + "..." if len(r["question"]) > 43 else r["question"],
            f"{r['duration']:.1f}s",
            notes,
        )

    console.print(table)

    if verbose:
        failures = [r for r in results if r["status"] == "FAIL" and r.get("response")]
        if failures:
            console.print("\n[bold red]Failed Responses:[/bold red]")
            for r in failures:
                resp = r["response"] or ""
                panel_content = resp[:500] + "..." if len(resp) > 500 else resp

                if r.get("llm_reasoning"):
                    panel_content += f"\n\n[dim]LLM Reasoning: {r['llm_reasoning']}[/dim]"

                console.print(
                    Panel(
                        panel_content,
                        title=f"[red]{r['question'][:60]}[/red]",
                        border_style="red",
                    )
                )


def display_summary(results: list[EvalResult], total_duration: float, category: str | None):
    """Display summary statistics."""
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    total = len(results)
    rate = (passed / total * 100) if total else 0

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()

    summary.add_row("Total:", f"{total} tests in {total_duration:.1f}s")
    summary.add_row("Passed:", Text(f"{passed} ({rate:.0f}%)", style="green"))
    summary.add_row("Failed:", Text(str(failed), style="red" if failed else "dim"))
    summary.add_row("Errors:", Text(str(errors), style="yellow" if errors else "dim"))
    summary.add_row("Avg time:", f"{total_duration / total:.1f}s per test" if total else "N/A")

    llm_grades: list[float] = [
        r["llm_grade"] for r in results if r.get("llm_grade") is not None and isinstance(r["llm_grade"], (int, float))
    ]
    if llm_grades:
        avg_grade = sum(llm_grades) / len(llm_grades)
        summary.add_row("Avg LLM Score:", f"{avg_grade:.2f}")

    console.print(
        Panel(
            summary,
            title="[bold]Summary[/bold]",
            border_style="green" if rate == 100 else "yellow",
        )
    )

    if not category and len(CATEGORIES) > 1:
        cat_table = Table(title="By Category", show_header=True)
        cat_table.add_column("Category")
        cat_table.add_column("Passed", justify="right")
        cat_table.add_column("Total", justify="right")
        cat_table.add_column("Rate", justify="right")

        for cat in CATEGORIES:
            cat_results = [r for r in results if r["category"] == cat]
            cat_passed = sum(1 for r in cat_results if r["status"] == "PASS")
            cat_total = len(cat_results)
            cat_rate = (cat_passed / cat_total * 100) if cat_total else 0

            rate_style = "green" if cat_rate == 100 else "yellow" if cat_rate >= 50 else "red"
            cat_table.add_row(
                cat,
                str(cat_passed),
                str(cat_total),
                Text(f"{cat_rate:.0f}%", style=rate_style),
            )

        console.print(cat_table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MCP agent evaluations")
    parser.add_argument("--category", "-c", choices=CATEGORIES, help="Filter by category")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full responses on failure")
    parser.add_argument(
        "--llm-grader",
        "-g",
        action="store_true",
        help="Use LLM to grade responses (requires OPENAI_API_KEY)",
    )
    args = parser.parse_args()

    run_evals(
        category=args.category,
        verbose=args.verbose,
        llm_grader=args.llm_grader,
    )
