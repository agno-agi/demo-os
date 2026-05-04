from agno.agent import Agent
from agno.workflow import Step, Workflow
from agno.workflow.loop import Loop
from agno.workflow.parallel import Parallel

from app.settings import MODEL, agent_db, get_parallel_tools
from utils.exa import get_exa_mcp_tools
from workflows.content_pipeline.instructions import (
    EDITOR_INSTRUCTIONS,
    OUTLINER_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
    WRITER_INSTRUCTIONS,
)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
researcher = Agent(
    id="content-pipeline-researcher",
    name="Content Researcher",
    model=MODEL,
    db=agent_db,
    tools=[*get_parallel_tools(), *get_exa_mcp_tools()],
    instructions=RESEARCHER_INSTRUCTIONS,
)

outliner = Agent(
    id="content-pipeline-outliner",
    name="Content Outliner",
    model=MODEL,
    db=agent_db,
    instructions=OUTLINER_INSTRUCTIONS,
)

writer = Agent(
    id="content-pipeline-writer",
    name="Content Writer",
    model=MODEL,
    db=agent_db,
    instructions=WRITER_INSTRUCTIONS,
    markdown=True,
)

editor = Agent(
    id="content-pipeline-editor",
    name="Content Editor",
    model=MODEL,
    db=agent_db,
    instructions=EDITOR_INSTRUCTIONS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def quality_check(outputs) -> bool:
    if not outputs:
        return False
    last_output = (outputs[-1].content or "").strip()
    if not last_output:
        return False
    last_line = last_output.split("\n")[-1]
    return last_line.strip(" \t*_`.!?,:;").upper() == "APPROVED"


# ---------------------------------------------------------------------------
# Create Workflow
# ---------------------------------------------------------------------------
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
