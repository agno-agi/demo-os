from os import getenv

from agno.agent import Agent
from agno.tools.coding import CodingTools
from agno.workflow import Step, Workflow

from app.settings import MODEL, agent_db
from workflows.repo_walkthrough.instructions import (
    ANALYST_INSTRUCTIONS,
    NARRATOR_INSTRUCTIONS,
    SCRIPT_WRITER_INSTRUCTIONS,
)

REPOS_DIR = getenv("REPOS_DIR", ".")

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
code_analyst = Agent(
    id="repo-walkthrough-analyst",
    name="Code Analyst",
    model=MODEL,
    db=agent_db,
    tools=[
        CodingTools(
            base_dir=REPOS_DIR,
            enable_read_file=True,
            enable_grep=True,
            enable_find=True,
            enable_ls=True,
            enable_edit_file=False,
            enable_write_file=False,
            enable_run_shell=False,
        ),
    ],
    instructions=ANALYST_INSTRUCTIONS,
)

script_writer = Agent(
    id="repo-walkthrough-scriptwriter",
    name="Script Writer",
    model=MODEL,
    db=agent_db,
    instructions=SCRIPT_WRITER_INSTRUCTIONS,
    markdown=True,
)

# Narrator — conditionally uses ElevenLabs TTS
narrator_tools: list = []
if getenv("ELEVEN_LABS_API_KEY"):
    from agno.tools.eleven_labs import ElevenLabsTools

    narrator_tools.append(ElevenLabsTools(enable_text_to_speech=True, voice_id="21m00Tcm4TlvDq8ikWAM"))

narrator = Agent(
    id="repo-walkthrough-narrator",
    name="Narrator",
    model=MODEL,
    db=agent_db,
    tools=narrator_tools,
    instructions=NARRATOR_INSTRUCTIONS,
)

# ---------------------------------------------------------------------------
# Create Workflow
# ---------------------------------------------------------------------------
repo_walkthrough = Workflow(
    id="repo-walkthrough",
    name="Repo Walkthrough",
    steps=[
        Step(name="Analyze", agent=code_analyst),
        Step(name="Script", agent=script_writer),
        Step(name="Narrate", agent=narrator),
    ],
)
