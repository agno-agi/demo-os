"""
Run AgentOS evals.

Usage:
    # Agno evals — LLM-judged via AgentAsJudgeEval and AccuracyEval
    python -m evals                              # All categories
    python -m evals --category security           # Single category
    python -m evals --verbose                     # Show judge reasoning

    # Smoke tests — fast pattern matching, no LLM cost
    python -m evals smoke                         # All entities
    python -m evals smoke --group agents           # By group
    python -m evals smoke --entity knowledge       # Single entity
    python -m evals smoke --verbose
    python -m evals smoke --output                 # Save results to disk

    # Reliability — tool call validation
    python -m evals reliability                    # All cases
    python -m evals reliability --entity voyager  # Single entity

    # Performance — latency baselines
    python -m evals perf                           # Compare against baselines
    python -m evals perf --update-baselines        # Establish baselines
    python -m evals perf --entity knowledge        # Single entity

    # Auto-improvement data collector
    python -m evals improve --entity knowledge
    python -m evals improve --failures
    python -m evals improve --entity knowledge --json

    # Global flags
    python -m evals --url http://prod.example.com
    python -m evals --timeout 180
    python -m evals smoke --output --compare       # Save + compare to last run
"""

import argparse
import sys

from evals.client import AgentOSClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AgentOS evals")
    subparsers = parser.add_subparsers(dest="command")

    # --- smoke ---
    smoke_parser = subparsers.add_parser("smoke", help="Fast pattern-matching smoke tests (no LLM cost)")
    smoke_parser.add_argument(
        "--group",
        type=str,
        help="Filter: agents, teams, workflows, security, graceful, hitl",
    )
    smoke_parser.add_argument("--entity", type=str, help="Filter by entity ID")
    smoke_parser.add_argument("--verbose", action="store_true", help="Show full responses")
    smoke_parser.add_argument("--url", type=str, help="Override base URL")
    smoke_parser.add_argument("--timeout", type=float, default=120.0, help="Default timeout (seconds)")
    smoke_parser.add_argument("--output", action="store_true", help="Save results to evals/.results/")
    smoke_parser.add_argument("--compare", action="store_true", help="Compare against last run")

    # --- reliability ---
    reliability_parser = subparsers.add_parser("reliability", help="Tool call validation evals")
    reliability_parser.add_argument("--entity", type=str, help="Filter by entity ID")
    reliability_parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    reliability_parser.add_argument("--url", type=str, help="Override base URL")
    reliability_parser.add_argument("--timeout", type=float, default=120.0, help="Default timeout (seconds)")
    reliability_parser.add_argument("--output", action="store_true", help="Save results to evals/.results/")

    # --- perf ---
    perf_parser = subparsers.add_parser("perf", help="Performance baseline tests")
    perf_parser.add_argument("--entity", type=str, help="Filter by entity ID")
    perf_parser.add_argument("--iterations", type=int, default=3, help="Runs per entity (default 3)")
    perf_parser.add_argument("--update-baselines", action="store_true", help="Save current results as baselines")
    perf_parser.add_argument("--url", type=str, help="Override base URL")
    perf_parser.add_argument("--timeout", type=float, default=120.0, help="Default timeout (seconds)")
    perf_parser.add_argument("--output", action="store_true", help="Save results to evals/.results/")

    # --- improve ---
    improve_parser = subparsers.add_parser("improve", help="Collect improvement data for Claude Code")
    improve_parser.add_argument("--entity", type=str, help="Entity ID to collect data for")
    improve_parser.add_argument(
        "--failures",
        action="store_true",
        help="Collect data for all failing entities",
    )
    improve_parser.add_argument("--url", type=str, help="Override base URL")
    improve_parser.add_argument("--timeout", type=float, default=120.0, help="Default timeout (seconds)")
    improve_parser.add_argument(
        "--container",
        type=str,
        default="agno-demo-api",
        help="Docker container name",
    )
    improve_parser.add_argument("--json", action="store_true", help="Output structured JSON")

    # --- top-level flags (default: run Agno evals) ---
    parser.add_argument("--category", type=str, help="Run a single eval category")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--url", type=str, help="Override base URL")
    parser.add_argument("--timeout", type=float, default=120.0, help="Default timeout (seconds)")
    parser.add_argument("--output", action="store_true", help="Save results to evals/.results/")

    args = parser.parse_args()

    if args.command == "smoke":
        from evals.smoke import run_smoke_tests

        client = AgentOSClient(base_url=args.url, timeout=args.timeout)
        results = run_smoke_tests(
            client,
            group=args.group,
            entity=args.entity,
            verbose=args.verbose,
        )

        if args.output:
            from evals.results import save_results

            path = save_results(results, "smoke")
            print(f"\nResults saved to {path}")

        if args.compare:
            from evals.results import load_latest, print_comparison

            previous = load_latest("smoke")
            if previous:
                print_comparison(results, previous["results"])
            else:
                print("\nNo previous smoke results to compare against.")

        has_failures = any(r["status"] in ("FAIL", "ERROR") for r in results)
        sys.exit(1 if has_failures else 0)

    elif args.command == "reliability":
        from evals.reliability import run_reliability_tests

        client = AgentOSClient(base_url=args.url, timeout=args.timeout)
        results = run_reliability_tests(
            client,
            entity=args.entity,
            verbose=args.verbose,
        )

        if args.output:
            from evals.results import save_results

            path = save_results(results, "reliability")
            print(f"\nResults saved to {path}")

        has_failures = any(r["status"] in ("FAIL", "ERROR") for r in results)
        sys.exit(1 if has_failures else 0)

    elif args.command == "perf":
        from evals.performance import run_performance_tests

        client = AgentOSClient(base_url=args.url, timeout=args.timeout)
        results = run_performance_tests(
            client,
            entity=args.entity,
            iterations=args.iterations,
            update_baselines=args.update_baselines,
        )

        if args.output:
            from evals.results import save_results

            path = save_results(results, "perf")
            print(f"\nResults saved to {path}")

        has_failures = any(r["status"] == "FAIL" for r in results)
        sys.exit(1 if has_failures else 0)

    elif args.command == "improve":
        from evals.improve import run_improve

        client = AgentOSClient(base_url=args.url, timeout=args.timeout)
        run_improve(
            client,
            entity_id=args.entity,
            failures_only=args.failures,
            docker_container=args.container,
            output_json=args.json,
        )

    else:
        # Default: run Agno evals (AgentAsJudgeEval, AccuracyEval)
        from evals.run import run_evals

        client = AgentOSClient(base_url=args.url, timeout=args.timeout)
        success = run_evals(
            client,
            category=args.category,
            verbose=args.verbose,
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
