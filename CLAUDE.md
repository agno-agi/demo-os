# CLAUDE.md

This file provides context for Claude Code when working with this repository.

## Project Overview

AgentOS - A multi-agent demo system built by Agno showcasing Agno framework features (6 agents, 4 teams, 5 workflows, 3 multi-framework agents).

## Architecture

```
AgentOS (app/main.py)
├── Agents (6)
│   ├── Sage (agents/mcp/)                                        # Agno documentation agent via MCP
│   ├── Voyager (agents/travel/)                            # Travel booking — HITL + guardrails
│   ├── Ledger (agents/approvals/)                            # Approval flows + audit trail
│   ├── Quill (agents/reporter/)                              # Web research + HTML report generation
│   ├── Iris (agents/studio/)                                  # Multimodal media (DALL-E, TTS, FAL, Luma)
│   └── Pilot (agents/taskboard/)                            # Session state + agentic state
├── Multi-Framework Agents (3)
│   ├── Probe (frameworks/claude_repo/)                 # Claude Agent SDK — explains GitHub repos
│   ├── Forum (frameworks/langgraph_debate/)                # LangGraph — parallel Pro/Con + Judge
│   └── Abacus (frameworks/dspy_math/)                      # DSPy — ChainOfThought word problems
├── Teams (4)
│   ├── Dash (agents/dash/)                                      # Data analyst (team, coordinate)
│   ├── Atlas (teams/research/)                    # Research team (coordinate mode)
│   ├── Chorus (teams/investment/)                 # Investment committee (broadcast mode)
│   └── Clinic (teams/clinic/)                     # Patient assistant (context provider + filtered records)
└── Workflows (5)
    ├── Dawn (workflows/morning_brief/)                 # Daily parallel briefing
    ├── Pulse (workflows/ai_research/)                     # Daily parallel AI research
    ├── Press (workflows/content_pipeline/)           # Parallel + loop + condition
    ├── Echo (workflows/repo_walkthrough/)                 # Code → script → narrated audio
    └── Beacon (workflows/support_triage/)               # Router + condition + escalation
```

All agents share:
- PostgreSQL database (pgvector) for persistence
- OpenAI GPT-5.4 model (configured in `app/settings.py`)
- Chat history and context management

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | AgentOS entry point, registers all agents, teams, workflows |
| `app/config.yaml` | Quick prompts for each agent |
| `app/settings.py` | Shared MODEL, agent_db, and environment flags |
| `app/registry.py` | Shared tools, models, and database connections |
| `agents/mcp/agent.py` | Sage - Agno documentation agent via live MCP tools |
| `agents/travel/agent.py` | Voyager - HITL + guardrails (moderation, PII, injection, output) |
| `agents/approvals/agent.py` | Ledger - approval flows + audit trail |
| `agents/reporter/agent.py` | Quill - web research (Exa) + HTML report generation |
| `agents/studio/agent.py` | Iris - multimodal media generation (DALL-E, FAL, ElevenLabs, Luma) |
| `agents/taskboard/agent.py` | Pilot - session state + agentic state demo |
| `frameworks/claude_repo/agent.py` | Probe - Claude Agent SDK with WebSearch/WebFetch |
| `frameworks/langgraph_debate/graph.py` | Forum - LangGraph graph with parallel branches |
| `frameworks/langgraph_debate/agent.py` | Forum - LangGraphAgent wrapper |
| `frameworks/dspy_math/agent.py` | Abacus - DSPyAgent with typed ChainOfThought signature |
| `agents/dash/team.py` | Dash team (Analyst, Engineer) |
| `teams/research/team.py` | Atlas (coordinate mode) |
| `teams/investment/team.py` | Chorus — investment committee (broadcast mode, 4 analysts, YFinance) |
| `teams/clinic/team.py` | Clinic — patient assistant (context provider + filtered records, followups, fallback) |
| `workflows/morning_brief/workflow.py` | Dawn (parallel gather → synthesize) |
| `workflows/ai_research/workflow.py` | Pulse (4 parallel researchers → synthesize) |
| `workflows/content_pipeline/workflow.py` | Press (router, parallel, loop, HITL) |
| `workflows/repo_walkthrough/workflow.py` | Echo (analyze → script → narrate) |
| `workflows/support_triage/workflow.py` | Beacon (classify → route → escalate) |
| `db/session.py` | `get_postgres_db()` and `create_knowledge()` helpers |
| `db/url.py` | Builds database URL from environment |
| `compose.yaml` | Local development with Docker |

## Development Setup

### Virtual Environment

Use the venv setup script to create the development environment:

```bash
./scripts/venv_setup.sh
source .venv/bin/activate
```

### Format & Validation

Always run format and lint checks using the venv Python interpreter:

```bash
source .venv/bin/activate && ./scripts/format.sh
source .venv/bin/activate && ./scripts/validate.sh
```

## Conventions

### Parameter Ordering

All Agent, Team, and Workflow constructors follow a strict parameter ordering convention.
When adding or editing constructors, always follow the group order below. Omit groups
that don't apply — but never reorder within or across groups.

**Agent parameter order:**

```
# Identity
id, name, role                          # role for team members only

# Model
model, reasoning, reasoning_min_steps,  # reasoning params if applicable
reasoning_max_steps, fallback_models

# Data
db, knowledge, search_knowledge

# Capabilities
tools, skills,                          # what the agent can do
learning, add_learnings_to_context      # how the agent improves

# Instructions
instructions                            # what to do with all the above

# Hooks
pre_hooks, post_hooks

# Feature-specific (group by feature)
dependencies, add_dependencies_to_context
session_state, enable_agentic_state, add_session_state_to_context
compress_tool_results, compression_manager

# Memory
enable_agentic_memory,
search_past_sessions, num_past_sessions_to_search

# Context
add_datetime_to_context, add_history_to_context,
read_chat_history, num_history_runs

# Output
markdown
```

**Team parameter order:**

```
# Identity
id, name, mode

# Model
model

# Members
members

# Data
db

# Capabilities
tools,
learning, add_learnings_to_context

# Instructions
instructions

# Collaboration
share_member_interactions, show_members_responses

# Memory
enable_agentic_memory,
search_past_sessions, num_past_sessions_to_search

# Context
add_datetime_to_context, add_history_to_context,
read_chat_history, num_history_runs

# Output
markdown
```

**Workflow parameter order:** `id`, `name`, `steps`

### Section Headers

All agent, team, and workflow files use `# ---` section headers to separate logical
blocks. Every file must have at least a `# Create Agent`, `# Create Team`, or
`# Create Workflow` header before the main constructor. Files with additional code
get descriptive headers for each block.

Common headers by file type:

| File Type | Headers |
|-----------|---------|
| Simple agent | `# Create Agent` |
| Agent with setup | `# Tools` / `# Dependencies` / `# Create Agent` |
| Agent with hooks | `# Hooks` (or descriptive name) / `# Create Agent` |
| Team with members | `# Members` / `# Create Team` |
| Team with setup | `# Team Leader Tools` / `# Instructions` / `# Members` / `# Create Team` |
| Workflow | `# Agents` / `# Helpers` (if any) / `# Create Workflow` |

Header format (75-char wide):
```python
# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
```

### Agent Pattern

All standalone agents follow this structure:

```python
from agno.agent import Agent

from agents.my_agent.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
my_agent = Agent(
    id="my-agent",
    name="My Agent",
    model=MODEL,
    db=agent_db,
    tools=[...],
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
```

### Team Pattern (Dash)

Team-based agents have their own settings.py with specialized knowledge bases and DB engines:

```python
from agno.team import Team, TeamMode

# ---------------------------------------------------------------------------
# Create Team
# ---------------------------------------------------------------------------
team = Team(
    id="my-team",
    name="My Team",
    mode=TeamMode.coordinate,
    model=MODEL,
    members=[agent1, agent2],
    db=agent_db,
    tools=[...],
    instructions=LEADER_INSTRUCTIONS,
    share_member_interactions=True,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    markdown=True,
)
```

### Database

- Use `get_postgres_db()` from `db` module
- **Important**: The `knowledge_table` parameter is only needed when the database is provided to a Knowledge base as a `contents_db`.

```python
# Agent WITH a Knowledge base
from db import create_knowledge
knowledge = create_knowledge("My Knowledge", "my_vectors")

# Agent WITHOUT a Knowledge base
agent_db = get_postgres_db()
```

- Knowledge bases use PgVector with `SearchType.hybrid`
- Embeddings use `text-embedding-3-small`

### Imports

```python
# Database
from db import db_url, get_postgres_db, create_knowledge

# Agents
from agents.mcp import mcp_agent
from agents.travel import travel
from agents.approvals import approvals
from agents.reporter import reporter
from agents.studio import studio
from agents.taskboard import taskboard

# Teams
from agents.dash import dash
from teams.research import research_coordinate
from teams.investment import investment_broadcast
from teams.clinic import clinic

# Workflows
from workflows.morning_brief import morning_brief
from workflows.ai_research import ai_research
from workflows.content_pipeline import content_pipeline
from workflows.repo_walkthrough import repo_walkthrough
from workflows.support_triage import support_triage
```

## Adding a New Agent

1. Create `agents/new_agent/` directory following the agent pattern above (with `agent.py`, `instructions.py`, `__init__.py`)
2. Register in `app/main.py`:
   ```python
   from agents.new_agent import new_agent

   agent_os = AgentOS(
       agents=[..., new_agent],
       ...
   )
   ```
3. Add quick prompts to `app/config.yaml` using the agent's `id`

## Commands

```bash
# Setup virtual environment
./scripts/venv_setup.sh
source .venv/bin/activate

# Local development with Docker
docker compose up -d --build

# Load knowledge for Dash
python -m agents.dash.scripts.load_knowledge

# Seed the Clinic team data (operational DB + patient records)
python -m teams.clinic.scripts.seed_clinic
python -m teams.clinic.scripts.load_records

# Format & validation (run from activated venv)
./scripts/format.sh
./scripts/validate.sh

# Run evals — smoke tests (fast, no LLM cost)
python -m evals smoke
python -m evals smoke --group agents
python -m evals smoke --group security
python -m evals smoke --group hitl
python -m evals smoke --entity docs
python -m evals smoke --output --compare

# Run evals — reliability (tool call validation, no LLM cost)
python -m evals reliability
python -m evals reliability --entity voyager

# Run evals — Agno evals (AgentAsJudgeEval, AccuracyEval — LLM cost)
python -m evals
python -m evals --category security
python -m evals --category accuracy
python -m evals --category quality
python -m evals --verbose

# Run evals — performance baselines
python -m evals perf --update-baselines
python -m evals perf

# Auto-improvement loop (see docs/EVALS.md for full workflow)
python -m evals improve --entity docs
python -m evals improve --failures
python -m evals improve --entity docs --json
```

## Environment Variables

Required:
- `OPENAI_API_KEY`

Optional (model providers — each enables registry models in Iris):
- `ANTHROPIC_API_KEY` - Claude Opus 4.7, Sonnet 4.6, Haiku 4.5
- `GOOGLE_API_KEY` - Gemini 3 Flash, Gemini 2.5 Pro
- `GROQ_API_KEY` - Llama 3.3 70B
- `DEEPSEEK_API_KEY` - DeepSeek Chat, DeepSeek Reasoner
- `XAI_API_KEY` - Grok 3
- `MISTRAL_API_KEY` - Mistral Large

Optional (tools & integrations):
- `EXA_API_KEY` - Web search for Quill, Pulse, Investment
- `PARALLEL_API_KEY` - Parallel web search
- `ELEVEN_LABS_API_KEY` - TTS for Iris, Echo
- `FAL_KEY` - Image-to-image for Iris
- `LUMAAI_API_KEY` - Video generation for Iris (LumaLab)
- `DB_DRIVER` - Database driver (default: `postgresql+psycopg`)
- `PORT` - API server port (default: `8000`)
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_DATABASE`
- `RUNTIME_ENV` - Set to `dev` for auto-reload, `prd` for RBAC auth
- `AGENTOS_URL` - Scheduler callback URL (default: `http://127.0.0.1:8000`)
- `SLACK_TOKEN`, `SLACK_SIGNING_SECRET` - Optional Slack interface (see `docs/SLACK_CONNECT.md`)

## Documentation

- `docs/EVALS.md` - Eval framework: smoke tests, reliability, accuracy, performance, improvement loop
- `docs/SLACK_CONNECT.md` - Slack setup: app manifest, scopes, credentials, SlackTools vs Interface

## Deployment

```bash
# Build Docker image
./scripts/build_image.sh

# Deploy to Railway (first time)
./scripts/railway_up.sh

# Redeploy to Railway
./scripts/railway_redeploy.sh

# Sync env vars to Railway
./scripts/railway_env.sh
```

## Ports

- API: 8000
- Database: 5432

## Feature Coverage

| Feature | Where |
|---------|-------|
| RAG / hybrid search | Dash, Investment |
| MCP tools | Sage, Dash, Pulse, Investment |
| HITL — confirmation | Voyager, Ledger |
| HITL — user input | Voyager |
| HITL — external execution | Voyager |
| Guardrails (moderation, PII, injection) | Voyager |
| Output guardrails | Voyager |
| Pre/post hooks | Voyager |
| User feedback (ask_user) | Voyager |
| Approval — blocking | Ledger |
| Approval — audit trail | Ledger |
| Reasoning tools | Dash |
| Structured output (Pydantic) | Quill |
| File generation (HTML) | Quill |
| Web research (Exa: search, company, crawl, fetch) | Quill |
| Learning (LearningMachine) | Dash, Investment |
| SQL tools | Dash |
| Coding tools | Echo |
| Image generation (DALL-E) | Iris |
| Image generation (Gemini NanoBanana) | Registry |
| Image-to-image (FAL) | Iris |
| Text-to-speech (ElevenLabs) | Iris, Echo |
| Video generation (LumaLab) | Iris |
| Sound effects | Iris |
| YFinance tools | Investment |
| Team — coordinate | Dash, Atlas |
| Team — broadcast | Chorus |
| Context provider (live DB) | Clinic |
| Knowledge filtering (per-patient) | Clinic |
| Followups (suggested questions) | Clinic |
| Fallback models | Clinic |
| Workflow — parallel | Dawn, Pulse, Press |
| Workflow — loop | Press |
| Scheduling (cron) | Dawn, Pulse |
| Parallel execution | Dawn, Pulse, Press |
| Workflow — router | Beacon |
| Workflow — condition | Beacon |
| Session state + agentic state | Pilot |
| Cross-modal chaining | Echo |

---

## Agno Framework Reference

### Model Providers

```python
from agno.models.openai import OpenAIResponses
model = OpenAIResponses(id="gpt-5.5")

from agno.models.anthropic import Claude
model = Claude(id="claude-sonnet-4-6")

from agno.models.google import Gemini
model = Gemini(id="gemini-3-flash-preview")
```

### Knowledge & RAG

```python
from agno.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

knowledge = Knowledge(
    name="My Knowledge Base",
    vector_db=PgVector(
        db_url=db_url,
        table_name="my_vectors",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    contents_db=get_postgres_db(knowledge_table="my_contents"),
)
```

### Documentation Links

- https://docs.agno.com/llms.txt
- https://docs.agno.com/llms-full.txt
- [Agno Docs](https://docs.agno.com)
