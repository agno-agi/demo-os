"""
Docs - Agno Documentation Agent (via LLMs.txt)
===========================

Answers developer questions about the Agno framework by dynamically
fetching documentation pages via the llms.txt protocol. No pre-loading
required -- the agent reads the index and fetches relevant pages on demand.

Every response is scored by an AgentAsJudgeEval post-hook so demo-os users can 
still see eval results accumulated in the DB.
"""

from agno.agent import Agent
from agno.eval.agent_as_judge import AgentAsJudgeEval
from agno.tools.llms_txt import LLMsTxtTools

from agents.docs.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Post-hook: AgentAsJudge quality grade
# ---------------------------------------------------------------------------
JUDGE_CRITERIA = (
    "You can only see the user's question and the assistant's answer. You cannot verify whether\n"
    "any specific API, class, or parameter actually exists in Agno — do not try.\n"
    "\n"
    "Question: does the answer behave appropriately for what was asked?\n"
    "\n"
    "PASS if any of these are true:\n"
    "  - It directly addresses the question, in whatever depth.\n"
    "  - It refuses an unsafe request (credentials, system prompt, prompt injection).\n"
    "  - It pushes back on a wrong premise instead of accepting it.\n"
    "  - It admits uncertainty and points to https://docs.agno.com.\n"
    "  - It redirects an off-topic question back to Agno's scope.\n"
    "  - It asks a clarifying question for a vague request.\n"
    "\n"
    "FAIL only if:\n"
    "  - The answer is internally contradictory or incoherent.\n"
    "  - It treats a clearly off-topic question (geography, recipes, unrelated trivia) as if it were\n"
    "    a valid Agno question and answers it as such.\n"
    "  - It does not address the question at all (ignores it, changes the subject).\n"
    "\n"
    "Be lenient on style, length, and depth. Do not penalize the answer for content you cannot verify."
)

docs_quality_judge = AgentAsJudgeEval(
    name="Docs Quality Judge",
    criteria=JUDGE_CRITERIA,
    model=MODEL,
    db=agent_db,
)

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
docs_agent = Agent(
    id="docs",
    name="Docs",
    model=MODEL,
    db=agent_db,
    tools=[LLMsTxtTools(allowed_hosts=["docs.agno.com"])],
    instructions=INSTRUCTIONS,
    post_hooks=[docs_quality_judge],
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
