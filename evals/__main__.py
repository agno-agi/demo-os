"""
Run evals.

Usage:
    python -m evals
    python -m evals --category security
    python -m evals --verbose
"""

import argparse
import sys

from evals.run import run_evals


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Agno Demo evals")
    parser.add_argument("--category", type=str, help="Run a single eval category")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    success = run_evals(category=args.category, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
