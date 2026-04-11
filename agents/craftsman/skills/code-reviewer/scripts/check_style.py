"""Automated Python style checker for the code-reviewer skill.

Checks basic style rules without requiring external dependencies.
Returns a list of findings as formatted strings.
"""


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
        if stripped.startswith("print(") and "# noqa" not in line:
            findings.append(f"{filename}:{i} — print() statement (use logging instead?)")

        # TODO/FIXME/HACK comments
        for tag in ("TODO", "FIXME", "HACK", "XXX"):
            if tag in line:
                findings.append(f"{filename}:{i} — {tag} comment found: {stripped}")

    # Function length check
    func_start = None
    func_name = None
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("def "):
            if func_start and func_name and (i - func_start) > 30:
                findings.append(f"{filename}:{func_start} — Function '{func_name}' is {i - func_start} lines (>30)")
            func_start = i
            func_name = stripped.split("(")[0].replace("def ", "")

    if not findings:
        return "No style issues found."
    return "\n".join(findings)
