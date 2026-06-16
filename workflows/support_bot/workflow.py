"""Troubleshooter - Agno step-level HITL troubleshooting workflow.

Takes an error as input, pauses to collect the user's environment via a step-level
HITL prompt, then searches the Agno docs, the web, and GitHub for a fix.

Demonstrates:
- Function step that captures the reported error
- Step-level HITL: a step that pauses before execution to collect the user's
  environment (Agno/Python version, OS, install method) via ``user_input_schema``
- Agent step that researches the fix (Agno docs MCP + web search + GitHub)
- HITL output review before the answer is finalized
- Function step that formats the final solution
"""

from agno.agent import Agent
from agno.tools.mcp import MCPTools
from agno.workflow import HumanReview, OnReject, Step, Workflow
from agno.workflow.types import StepInput, StepOutput

from app.settings import MODEL
from utils.exa import get_exa_mcp_tools
from workflows.support_bot.instructions import RESOLVER_INSTRUCTIONS, SEARCHER_INSTRUCTIONS

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
searcher = Agent(
    name="Support Searcher",
    model=MODEL,
    # Live Agno docs (MCP) + web search (Exa). The agent searches GitHub via the web tool.
    tools=[MCPTools(url="https://docs.agno.com/mcp"), *get_exa_mcp_tools("web_search_exa")],
    instructions=SEARCHER_INSTRUCTIONS,
)

resolver = Agent(
    name="Support Resolver",
    model=MODEL,
    instructions=RESOLVER_INSTRUCTIONS,
    markdown=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def capture_error(step_input: StepInput) -> StepOutput:
    """Capture the reported error before collecting environment details."""
    error = str(step_input.input or "").strip() or "(no error provided)"
    return StepOutput(content=f"Reported error:\n{error}")


def collect_environment(step_input: StepInput) -> StepOutput:
    """Fold the human-supplied environment details into the troubleshooting context."""
    error_context = str(step_input.previous_step_content or "").strip()
    user_input = step_input.additional_data.get("user_input", {}) if step_input.additional_data else {}
    agno_version = str(user_input.get("agno_version") or "unknown").strip()
    python_version = str(user_input.get("python_version") or "unknown").strip()
    os_name = str(user_input.get("os") or "unknown").strip()
    install_method = str(user_input.get("install_method") or "unknown").strip()
    extra = str(user_input.get("details") or "").strip()

    lines = [
        error_context,
        "",
        "Environment:",
        f"- Agno version: {agno_version}",
        f"- Python version: {python_version}",
        f"- OS: {os_name}",
        f"- Install method: {install_method}",
    ]
    if extra:
        lines.append(f"- Additional details: {extra}")
    return StepOutput(content="\n".join(lines))


def format_solution(step_input: StepInput) -> StepOutput:
    """Wrap the resolved answer in a clear deliverable section."""
    content = step_input.previous_step_content or "No solution generated"
    return StepOutput(content=f"=== PROPOSED SOLUTION ===\n\n{content}\n\n=== END ===")


# ---------------------------------------------------------------------------
# Create Workflow
# ---------------------------------------------------------------------------
support_bot = Workflow(
    id="troubleshooter",
    name="Troubleshooter",
    description=(
        "Agno troubleshooting bot — captures an error, collects your environment via step-level HITL, "
        "then searches docs, the web, and GitHub for a fix."
    ),
    steps=[
        Step(name="capture_error", executor=capture_error),
        Step(
            name="collect_environment",
            step_id="collect_environment",
            executor=collect_environment,
            requires_user_input=True,
            user_input_message="To diagnose this, share a few details about your setup:",
            user_input_schema=[
                {
                    "name": "agno_version",
                    "field_type": "str",
                    "description": "Your Agno version (e.g. '2.6.14'). Run `pip show agno` if unsure.",
                    "required": True,
                },
                {
                    "name": "python_version",
                    "field_type": "str",
                    "description": "Your Python version (e.g. '3.12').",
                    "required": True,
                },
                {
                    "name": "os",
                    "field_type": "str",
                    "description": "Operating system (e.g. 'macOS 14', 'Ubuntu 22.04', 'Windows 11').",
                    "required": False,
                },
                {
                    "name": "install_method",
                    "field_type": "str",
                    "description": "How you installed Agno: 'pip', 'uv', 'poetry', or 'docker'.",
                    "required": False,
                },
                {
                    "name": "details",
                    "field_type": "str",
                    "description": "Anything else relevant — full traceback, what you were doing, recent changes.",
                    "required": False,
                },
            ],
        ),
        Step(name="search", agent=searcher),
        Step(
            name="resolve",
            agent=resolver,
            human_review=HumanReview(
                requires_output_review=True,
                output_review_message="Review the proposed solution before it's finalized.",
                on_reject=OnReject.cancel,
            ),
        ),
        Step(name="format_solution", executor=format_solution),
    ],
)
