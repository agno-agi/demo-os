"""Content Generation HITL - step-level user input workflow demo.

Demonstrates:
- Function step that prepares topic context
- Function step that pauses for user content requirements
- Agent step that researches the topic with web search
- Agent step that generates content from the research brief
- HITL output review before final formatting
- Function step that formats the final generated content
"""

from agno.agent import Agent
from agno.workflow import HumanReview, OnReject, Step, Workflow
from agno.workflow.types import StepInput, StepOutput

from app.settings import MODEL
from utils.exa import get_exa_mcp_tools
from workflows.content_generation_hitl.instructions import CONTENT_GENERATOR_INSTRUCTIONS, RESEARCHER_INSTRUCTIONS

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
researcher = Agent(
    name="Content Researcher",
    model=MODEL,
    tools=[*get_exa_mcp_tools("web_search_exa")],
    instructions=RESEARCHER_INSTRUCTIONS,
)

content_generator = Agent(
    name="Content Generator",
    model=MODEL,
    instructions=CONTENT_GENERATOR_INSTRUCTIONS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def gather_context(step_input: StepInput) -> StepOutput:
    """Prepare the content topic before collecting generation preferences."""
    topic = str(step_input.input or "").strip() or "general topic"
    return StepOutput(content=(f"Topic: {topic}\nReady to collect content requirements."))


def get_user_requirements(step_input: StepInput) -> StepOutput:
    """Normalize human content preferences for downstream research and generation."""
    topic_context = str(step_input.previous_step_content or "").strip()
    user_input = step_input.additional_data.get("user_input", {}) if step_input.additional_data else {}
    audience = str(user_input.get("audience") or "general audience").strip()
    content_format = str(user_input.get("format") or "content draft").strip()
    tone = str(user_input.get("tone") or "use a suitable tone").strip()
    length = str(user_input.get("length") or "use a suitable length").strip()
    include_examples = user_input.get("include_examples", False)

    return StepOutput(
        content=(
            f"{topic_context}\n\n"
            "Content requirements:\n"
            f"- audience: {audience}\n"
            f"- format: {content_format}\n"
            f"- tone: {tone}\n"
            f"- length: {length}\n"
            f"- include_examples: {include_examples}"
        )
    )


def format_output(step_input: StepInput) -> StepOutput:
    """Wrap the generated content in a concise deliverable section."""
    content = step_input.previous_step_content or "No content generated"
    return StepOutput(content=f"=== GENERATED CONTENT ===\n\n{content}\n\n=== END ===")


# ---------------------------------------------------------------------------
# Create Workflow
# ---------------------------------------------------------------------------
content_generation_hitl = Workflow(
    id="content-generation-hitl",
    name="Content Generation HITL",
    description=(
        "Generates content by collecting human requirements, researching the topic, and drafting the final output."
    ),
    steps=[
        Step(name="gather_context", executor=gather_context),
        Step(
            name="get_user_requirements",
            step_id="get_user_requirements",
            executor=get_user_requirements,
            requires_user_input=True,
            user_input_message="Please provide your content preferences:",
            user_input_schema=[
                {
                    "name": "audience",
                    "field_type": "str",
                    "description": "Target audience, such as developers, executives, or new users",
                    "required": True,
                },
                {
                    "name": "format",
                    "field_type": "str",
                    "description": "Content format, such as blog intro, email, launch post, or social thread",
                    "required": True,
                },
                {
                    "name": "tone",
                    "field_type": "str",
                    "description": "Tone of the content: 'formal', 'casual', or 'technical'",
                    "required": False,
                },
                {
                    "name": "length",
                    "field_type": "str",
                    "description": "Content length: 'short' (1 para), 'medium' (3 para), or 'long' (5+ para)",
                    "required": False,
                },
                {
                    "name": "include_examples",
                    "field_type": "bool",
                    "description": "Include practical examples?",
                    "required": False,
                },
            ],
        ),
        Step(name="research", agent=researcher),
        Step(
            name="generate_content",
            agent=content_generator,
            human_review=HumanReview(
                requires_output_review=True,
                output_review_message="Review and optionally edit the generated content before final formatting.",
                on_reject=OnReject.cancel,
            ),
        ),
        Step(name="format_output", executor=format_output),
    ],
)
