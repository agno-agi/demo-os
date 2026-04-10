from agno.agent import Agent
from agno.tools.parallel import ParallelTools
from agno.workflow import Step, Workflow
from agno.workflow.loop import Loop
from agno.workflow.parallel import Parallel

from app.settings import MODEL, agent_db
from utils.exa import get_exa_mcp_tools
from workflows.content_pipeline.instructions import (
    EDITOR_INSTRUCTIONS,
    OUTLINER_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
    WRITER_INSTRUCTIONS,
)

researcher = Agent(
    name="Content Researcher",
    model=MODEL,
    db=agent_db,
    tools=[ParallelTools(), *get_exa_mcp_tools()],
    instructions=RESEARCHER_INSTRUCTIONS,
)

outliner = Agent(
    name="Content Outliner",
    model=MODEL,
    db=agent_db,
    instructions=OUTLINER_INSTRUCTIONS,
)

writer = Agent(
    name="Content Writer",
    model=MODEL,
    db=agent_db,
    instructions=WRITER_INSTRUCTIONS,
    markdown=True,
)

editor = Agent(
    name="Content Editor",
    model=MODEL,
    db=agent_db,
    instructions=EDITOR_INSTRUCTIONS,
)


def quality_check(outputs) -> bool:
    """End the loop if the editor approves (score >= 8)."""
    if not outputs:
        return False
    last_output = outputs[-1].content if outputs else ""
    return "APPROVED" in (last_output or "").upper()


content_pipeline = Workflow(
    id="content-pipeline",
    name="Content Pipeline",
    steps=[
        Parallel(
            Step(name="Research", agent=researcher),  # type: ignore[arg-type]
            Step(name="Outline", agent=outliner),  # type: ignore[arg-type]
            name="Research & Outline",
        ),
        Loop(
            name="Draft & Review",
            steps=[
                Step(name="Write Draft", agent=writer),
                Step(name="Editorial Review", agent=editor),
            ],
            end_condition=quality_check,
            max_iterations=3,
        ),
    ],
)
