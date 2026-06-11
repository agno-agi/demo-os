"""Content Generation HITL - step-level user input workflow demo.

Demonstrates:
- Function step that prepares topic context
- Agent step that pauses for user preferences before generation
- Function step that formats the final generated content
"""

from agno.agent import Agent
from agno.workflow import Step, Workflow
from agno.workflow.types import StepInput, StepOutput

from app.settings import MODEL
from workflows.content_generation_hitl.instructions import CONTENT_GENERATOR_INSTRUCTIONS

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
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
    return StepOutput(
        content=(f"Context gathered for: '{topic}'\nReady to generate content based on user preferences.")
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
    steps=[
        Step(name="gather_context", executor=gather_context),
        Step(
            name="generate_content",
            step_id="generate_content123",
            agent=content_generator,
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
        Step(name="format_output", executor=format_output),
    ],
)
