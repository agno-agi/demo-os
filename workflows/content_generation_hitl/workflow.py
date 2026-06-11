"""Content Generation HITL - step-level user input workflow demo.

Demonstrates:
- Function step that prepares topic context
- Agent step that pauses for user preferences before generation
- Function step that formats the final generated content
"""

from agno.agent import Agent
from agno.workflow import Step, Workflow
from agno.workflow.types import StepInput, StepOutput

from app.settings import MODEL, agent_db
from workflows.content_generation_hitl.instructions import CONTENT_GENERATOR_INSTRUCTIONS

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
content_generator = Agent(
    id="content-generation-writer",
    name="Content Generation Writer",
    model=MODEL,
    db=agent_db,
    instructions=CONTENT_GENERATOR_INSTRUCTIONS,
    markdown=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def gather_context(step_input: StepInput) -> StepOutput:
    """Prepare the content topic before collecting generation preferences."""
    topic = str(step_input.input or "").strip() or "a product update"
    return StepOutput(
        content=(
            f"Topic: {topic}\n\n"
            "Use the next step's user preferences to decide the audience, format, tone, length, and examples."
        )
    )


def format_output(step_input: StepInput) -> StepOutput:
    """Wrap the generated content in a concise deliverable section."""
    content = str(step_input.previous_step_content or "").strip()
    if not content:
        content = "No content was generated."
    return StepOutput(content=f"## Generated Content\n\n{content}")


# ---------------------------------------------------------------------------
# Create Workflow
# ---------------------------------------------------------------------------
content_generation_hitl = Workflow(
    id="content-generation-hitl",
    name="Content Generation HITL",
    steps=[
        Step(name="Gather Context", executor=gather_context),
        Step(
            name="Generate Content",
            agent=content_generator,
            requires_user_input=True,
            user_input_message="Choose the content preferences before generation.",
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
                    "description": "Tone of voice, such as concise, friendly, technical, or executive",
                    "required": True,
                },
                {
                    "name": "length",
                    "field_type": "str",
                    "description": "Desired length, such as short, medium, or long",
                    "required": True,
                },
                {
                    "name": "include_examples",
                    "field_type": "bool",
                    "description": "Whether to include practical examples",
                    "required": False,
                },
            ],
        ),
        Step(name="Format Output", executor=format_output),
    ],
)
