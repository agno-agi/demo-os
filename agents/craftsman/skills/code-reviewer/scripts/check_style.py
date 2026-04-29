#!/usr/bin/env python3
"""Automated Python style checker for the code-reviewer skill.

Checks basic style rules without requiring external dependencies.
Returns a list of findings as formatted strings.
"""

import argparse


def check_style(code: str, filename: str = "<input>") -> str:
    """Check Python code for common style issues.

    Args:
        code: The source code to check.
        filename: Optional filename for reporting.

    Returns:
        Formatted string of findings, or "No style issues found." if clean.
    """
    findings: list[str] = []
    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        # Line length
        if len(line) > 120:
            findings.append(f"{filename}:{i} — Line exceeds 120 characters ({len(line)} chars)")

        # Trailing whitespace
        if line != line.rstrip():
            findings.append(f"{filename}:{i} — Trailing whitespace")

        # Tab indentation
        if line.startswith("\t"):
            findings.append(f"{filename}:{i} — Tab indentation (use spaces)")

        # Bare except
        stripped = line.strip()
        if stripped == "except:" or stripped == "except :":
            findings.append(f"{filename}:{i} — Bare except clause (catch specific exceptions)")

        # Print statements (potential debug leftover)
        if stripped.startswith("print(") and not any(tag in line for tag in ("# noqa", "# audit")):
            findings.append(f"{filename}:{i} — print() statement (use logging instead?)")

        # TODO/FIXME/HACK comments
        for tag in ("TODO", "FIXME", "HACK", "XXX"):
            if tag in line:
                findings.append(f"{filename}:{i} — {tag} comment found: {stripped}")

    # Function length check — collect every def, then measure each uniformly.
    defs: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("async def "):
            name = stripped.split("(")[0].replace("async def ", "").replace("def ", "")
            defs.append((i, name))

    # Ignore trailing empty lines so a file ending in "\n" doesn't over-count.
    last_real = len(lines)
    while last_real > 0 and not lines[last_real - 1].strip():
        last_real -= 1

    for idx, (start, name) in enumerate(defs):
        end = defs[idx + 1][0] - 1 if idx + 1 < len(defs) else last_real
        length = end - start + 1
        if length > 30:
            findings.append(f"{filename}:{start} — Function '{name}' is {length} lines (>30)")

    if not findings:
        return "No style issues found."
    return "\n".join(findings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Python code for style issues.")
    parser.add_argument("code", help="Python code to check.")
    args = parser.parse_args()
    print(check_style(args.code))
