# AGENTS.md

This file provides context for Codex when working with this repository.

## Project Overview

AgentOS - A multi-agent demo system built by Agno showcasing 50+ Agno framework features (14 agents, 11 teams, 5 workflows).

## Architecture

```
AgentOS (app/main.py)
├── Agents (14)
│   ├── Docs (agents/docs/)                                      # LLMs.txt documentation agent
│   ├── MCP (agents/mcp/)                                        # External tools via MCP
│   ├── Helpdesk (agents/helpdesk/)                              # HITL + guardrails demo
│   ├── Feedback (agents/feedback/)                              # User feedback + control flow
│   ├── Approvals (agents/approvals/)                            # Approval flows + audit trail
│   ├── Reasoner (agents/reasoner/)                              # Reasoning + multi-model + fallback
│   ├── Reporter (agents/reporter/)                              # Structured output + file generation
│   ├── Contacts (agents/contacts/)                              # Entity memory + relationships
│   ├── Studio (agents/studio/)                                  # Multimodal media (DALL-E, TTS, FAL, Luma)
│   ├── Scheduler (agents/scheduler/)                            # Schedule management (SchedulerTools)
│   ├── Taskboard (agents/taskboard/)                            # Session state + agentic state
│   ├── Compressor (agents/compressor/)                          # Tool result compression
│   ├── Injector (agents/injector/)                              # Dependency injection via RunContext
│   └── Craftsman (agents/craftsman/)                            # Skills system (LocalSkills)
├── Teams (10)
│   ├── Pal (agents/pal/)                                        # Personal knowledge agent (team)
│   ├── Dash (agents/dash/)                                      # Data analyst (team)
│   ├── Research Coordinate (teams/research/)                    # Team coordinate mode
│   ├── Research Route (teams/research/)                         # Team route mode
│   ├── Research Broadcast (teams/research/)                     # Team broadcast mode
│   ├── Research Tasks (teams/research/)                         # Team tasks mode
│   ├── Investment Coordinate (teams/investment/)                # Investment team coordinate
│   ├── Investment Route (teams/investment/)                     # Investment team route
│   ├── Investment Broadcast (teams/investment/)                 # Investment team broadcast
│   └── Investment Tasks (teams/investment/)                     # Investment team tasks
└── Workflows (5)
    ├── Morning Brief (workflows/morning_brief/)                 # Daily parallel briefing
    ├── AI Research (workflows/ai_research/)                     # Daily parallel AI research
    ├── Content Pipeline (workflows/content_pipeline/)           # Parallel + loop + condition
    ├── Repo Walkthrough (workflows/repo_walkthrough/)           # Code → script → narrated audio
    └── Support Triage (workflows/support_triage/)               # Router + condition + escalation
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
| `agents/docs/agent.py` | Docs - Agno documentation agent using LLMs.txt tools |
| `agents/mcp/agent.py` | MCP - Agno documentation agent via live MCP tools |
| `agents/helpdesk/agent.py` | Helpdesk - HITL + guardrails (moderation, PII, injection, output) |
| `agents/feedback/agent.py` | Feedback - user feedback + control flow tools |
| `agents/approvals/agent.py` | Approvals - approval flows + audit trail |
| `agents/reasoner/agent.py` | Reasoner - reasoning + multi-model + fallback |
| `agents/reporter/agent.py` | Reporter - structured output + file generation |
| `agents/contacts/agent.py` | Contacts - entity memory + relationships |
| `agents/studio/agent.py` | Studio - multimodal media generation (DALL-E, FAL, ElevenLabs, Luma) |
| `agents/scheduler/agent.py` | Scheduler - schedule management (create, list, enable/disable, delete) |
| `agents/taskboard/agent.py` | Taskboard - session state + agentic state demo |
| `agents/compressor/agent.py` | Compressor - tool result compression with CompressionManager |
| `agents/injector/agent.py` | Injector - dependency injection via RunContext |
| `agents/craftsman/agent.py` | Craftsman - Skills system with LocalSkills loader |
| `agents/pal/team.py` | Pal team (Navigator, Researcher, Compiler, Linter, Syncer) |
| `agents/dash/team.py` | Dash team (Analyst, Engineer) |
| `teams/research/team.py` | Research Team (4 modes: coordinate, route, broadcast, tasks) |
| `teams/investment/team.py` | Investment Team (4 modes, 7 agents, YFinance) |
| `workflows/morning_brief/workflow.py` | Morning Brief (parallel gather → synthesize) |
| `workflows/ai_research/workflow.py` | AI Research (4 parallel researchers → synthesize) |
| `workflows/content_pipeline/workflow.py` | Content Pipeline (router, parallel, loop, HITL) |
| `workflows/repo_walkthrough/workflow.py` | Repo Walkthrough (analyze → script → narrate) |
| `workflows/support_triage/workflow.py` | Support Triage (classify → route → escalate) |
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

### Team Pattern (Pal, Dash)

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
from agents.docs import docs_agent
from agents.mcp import mcp_agent
from agents.helpdesk import helpdesk
from agents.feedback import feedback
from agents.approvals import approvals
from agents.reasoner import reasoner
from agents.reporter import reporter
from agents.contacts import contacts
from agents.studio import studio
from agents.scheduler import scheduler
from agents.taskboard import taskboard
from agents.compressor import compressor
from agents.injector import injector
from agents.craftsman import craftsman

# Teams
from agents.pal import pal
from agents.dash import dash
from teams.research import research_coordinate, research_route, research_broadcast, research_tasks
from teams.investment import investment_coordinate, investment_route, investment_broadcast, investment_tasks

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
python -m evals reliability --entity helpdesk

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

Optional (model providers — each enables registry models in Studio):
- `ANTHROPIC_API_KEY` - Codex Sonnet 4.5, Haiku 4.5 + Reasoner fallback
- `GOOGLE_API_KEY` - Gemini 3 Flash, Gemini 2.5 Pro
- `GROQ_API_KEY` - Llama 3.3 70B
- `DEEPSEEK_API_KEY` - DeepSeek Chat, DeepSeek Reasoner
- `XAI_API_KEY` - Grok 3
- `MISTRAL_API_KEY` - Mistral Large

Optional (tools & integrations):
- `EXA_API_KEY` - Web search for Reasoner, AI Research, Reporter, Contacts
- `PARALLEL_API_KEY` - Parallel web search (Pal Researcher)
- `ELEVENLABS_API_KEY` - TTS for Studio, Repo Walkthrough
- `FAL_KEY` - Image-to-image for Studio
- `LUMAAI_API_KEY` - Video generation for Studio (LumaLab)
- `DB_DRIVER` - Database driver (default: `postgresql+psycopg`)
- `PORT` - API server port (default: `8000`)
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_DATABASE`
- `RUNTIME_ENV` - Set to `dev` for auto-reload, `prd` for RBAC auth
- `AGENTOS_URL` - Scheduler callback URL (default: `http://127.0.0.1:8000`)
- `SLACK_TOKEN`, `SLACK_SIGNING_SECRET` - Optional Slack interface (see `docs/SLACK_CONNECT.md`)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PROJECT_ID` - Pal Gmail/Calendar
- `GITHUB_ACCESS_TOKEN`, `PAL_REPO_URL` - Pal Git sync

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
| RAG / hybrid search | Pal, Dash, Investment |
| LLMs.txt tools | Docs |
| MCP tools | MCP, Pal, Dash, AI Research, Investment |
| HITL — confirmation | Helpdesk, Approvals |
| HITL — user input | Helpdesk, Feedback |
| HITL — external execution | Helpdesk |
| Guardrails (moderation, PII, injection) | Helpdesk |
| Output guardrails | Helpdesk |
| Pre/post hooks | Helpdesk |
| Approval — blocking | Approvals |
| Approval — audit trail | Approvals |
| User feedback (ask_user) | Feedback |
| User control flow | Feedback |
| Reasoning tools | Reasoner |
| Native reasoning mode | Reasoner |
| Model fallback | Reasoner |
| Structured output (Pydantic) | Reporter |
| File generation (CSV/JSON/PDF) | Reporter |
| Entity memory | Contacts |
| User profile | Contacts |
| Session context + planning | Contacts |
| Learning (LearningMachine) | Pal, Dash, Contacts, Investment |
| SQL tools | Dash, Pal |
| Coding tools | Repo Walkthrough |
| Image generation (DALL-E) | Studio |
| Image-to-image (FAL) | Studio |
| Text-to-speech (ElevenLabs) | Studio, Repo Walkthrough |
| Video generation (LumaLab) | Studio |
| Sound effects | Studio |
| YFinance tools | Investment |
| File tools (memos) | Investment |
| Team — coordinate | Pal, Dash, Research, Investment |
| Team — route | Research, Investment |
| Team — broadcast | Research, Investment |
| Team — tasks | Research, Investment |
| Workflow — parallel | Morning Brief, AI Research, Content Pipeline |
| Workflow — loop | Content Pipeline |
| Scheduling (cron) | Morning Brief, AI Research, Scheduler |
| SchedulerTools (CRUD) | Scheduler |
| Parallel execution | Morning Brief, AI Research, Content Pipeline |
| Workflow — router | Support Triage |
| Workflow — condition | Support Triage |
| Session state + agentic state | Taskboard |
| Tool result compression | Compressor |
| Dependency injection (RunContext) | Injector |
| Skills system (LocalSkills) | Craftsman |
| Cross-modal chaining | Repo Walkthrough |

---

## Agno Framework Reference

### Model Providers

```python
from agno.models.openai import OpenAIResponses
model = OpenAIResponses(id="gpt-5.4")

from agno.models.anthropic import Codex
model = Codex(id="Codex-sonnet-4-5")

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
