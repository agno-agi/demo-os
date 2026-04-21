# Demo AgentOS

A reference AgentOS application built with Agno.

This repo packages a broad set of agent patterns into one runnable system: standalone agents, multi-agent teams, scheduled workflows, shared memory, guardrails, approvals, and external integrations. You can run it locally, inspect each example in isolation, and use it as a starting point for your own AgentOS.

The architecture is intentionally simple. Fourteen agents, eleven teams, and five workflows run inside one FastAPI service with PostgreSQL for persistence and shared context. The goal is not to show off a feature checklist. It is to show how agentic systems can be built with ordinary application architecture, clear boundaries, and production-minded patterns.

Use this project to:

1. **See how core Agno patterns fit together in a single app.**
2. **Explore working examples of memory, RAG, tool use, scheduling, guardrails, and collaboration modes.**
3. **Extend the system with your own agents, teams, workflows, and integrations.**

## Quick Start

```sh
# Clone the repo
git clone https://github.com/agno-agi/demo-os.git demo-os
cd demo-os

cp example.env .env
# Edit .env and add your OPENAI_API_KEY

# Start the application
docker compose up -d --build

# Load SaaS data for Dash
docker exec -it demo-os-api python -m agents.dash.scripts.load_data
docker exec -it demo-os-api python -m agents.dash.scripts.load_knowledge
```

Confirm the system is running at [http://localhost:8000/docs](http://localhost:8000/docs).

### Connect to the Web UI

1. Open [os.agno.com](https://os.agno.com) and login
2. Add OS -> Local -> `http://localhost:8000`
3. Click "Connect"

## What's Inside

### Agents

| Agent | What it does | Features |
|-------|-------------|----------|
| [**Docs**](agents/docs/) | Answers questions about Agno using live documentation | LLMs.txt tools, on-demand fetching |
| [**MCP**](agents/mcp/) | Queries live Agno docs via MCP server | Model Context Protocol |
| [**Helpdesk**](agents/helpdesk/) | IT operations helpdesk with safety guardrails | HITL (confirmation, user input, external execution), PII + injection guardrails, pre/post hooks |
| [**Feedback**](agents/feedback/) | Planning concierge with structured questions | UserFeedbackTools, UserControlFlowTools |
| [**Approvals**](agents/approvals/) | Compliance agent gating sensitive operations | @approval decorator, blocking confirmation, audit trail |
| [**Reasoner**](agents/reasoner/) | Strategic analysis with step-by-step reasoning | ReasoningTools, native reasoning mode, model fallback (Claude) |
| [**Reporter**](agents/reporter/) | On-demand report generator | FileGenerationTools (CSV/JSON/PDF), CalculatorTools, structured output |
| [**Contacts**](agents/contacts/) | Relationship intelligence / mini CRM | Entity memory, user profile, session context, LearningMachine |
| [**Studio**](agents/studio/) | Multimodal media generation and analysis | DalleTools, FalTools, ElevenLabsTools, LumaLabTools, conditional tool loading |
| [**Scheduler**](agents/scheduler/) | Schedule management for recurring tasks | SchedulerTools (create, list, enable/disable, delete schedules) |
| [**Taskboard**](agents/taskboard/) | Task management with persistent session state | Session state, agentic state, CRUD tools |
| [**Compressor**](agents/compressor/) | Web research with tool result compression | CompressionManager, DuckDuckGo, Exa MCP |
| [**Injector**](agents/injector/) | Configuration queries via dependency injection | RunContext, dependencies, feature flags |
| [**Craftsman**](agents/craftsman/) | Domain-specific expert guidance via skills | LocalSkills (code-reviewer, api-designer, prompt-engineer) |

### Teams

| Team | Mode | What it does | Features |
|------|------|-------------|----------|
| [**Pal**](agents/pal/) | coordinate | Personal knowledge agent (5 specialist agents) | SQL tools, file tools, wiki pipeline, web research, git sync |
| [**Dash**](agents/dash/) | coordinate | Self-learning data analyst (Analyst + Engineer) | Dual schema, write guard, read-only engine, LearningMachine |
| [**Research**](teams/research/) | coordinate, route, broadcast, tasks | Research team demonstrating all 4 team modes | ParallelTools, Exa MCP, team mode comparison |
| [**Investment**](teams/investment/) | coordinate, route, broadcast, tasks | 7-agent investment committee using Gemini | Multi-model (Gemini), YFinanceTools, FileTools, LearningMachine |

### Workflows

| Workflow | Schedule | What it does | Features |
|----------|----------|-------------|----------|
| [**Morning Brief**](workflows/morning_brief/) | Weekdays 8am ET | Parallel gather (calendar + email + news) then synthesize | Workflow, Step, Parallel, mock tools |
| [**AI Research**](workflows/ai_research/) | Daily 7am UTC | 4 parallel researchers then synthesize | Workflow, Parallel, Exa MCP |
| [**Content Pipeline**](workflows/content_pipeline/) | On demand | Research + outline, then draft/review loop (max 3 iterations) | Workflow, Parallel, Loop, end condition |
| [**Repo Walkthrough**](workflows/repo_walkthrough/) | On demand | Analyze code -> write script -> narrate with TTS | Workflow, CodingTools, ElevenLabsTools, cross-modal chaining |
| [**Support Triage**](workflows/support_triage/) | On demand | Classify tickets, route to specialist, escalate if critical | Workflow, Router, Condition, escalation |

### Feature Coverage

| Feature | Where |
|---------|-------|
| RAG / hybrid search | Pal, Dash |
| LLMs.txt tools | Docs |
| MCP tools | MCP, Pal, Dash, AI Research |
| HITL — confirmation | Helpdesk, Approvals |
| HITL — user input | Helpdesk, Feedback |
| HITL — external execution | Helpdesk |
| Guardrails (PII, injection) | Helpdesk |
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
| Learning (LearningMachine) | Pal, Dash, Contacts, Investment |
| SQL tools | Dash, Pal |
| Coding tools | Repo Walkthrough |
| Image generation (DALL-E) | Studio |
| Image-to-image (FAL) | Studio |
| Text-to-speech (ElevenLabs) | Studio, Repo Walkthrough |
| Video generation (LumaLab) | Studio |
| Multi-model (Gemini) | Investment |
| YFinance tools | Investment |
| Session state + agentic state | Taskboard |
| Tool result compression | Compressor |
| Dependency injection (RunContext) | Injector |
| Skills system (LocalSkills) | Craftsman |
| Team — coordinate | Pal, Dash, Research, Investment |
| Team — route | Research, Investment |
| Team — broadcast | Research, Investment |
| Team — tasks | Research, Investment |
| Workflow — parallel | Morning Brief, AI Research, Content Pipeline |
| Workflow — loop | Content Pipeline |
| Workflow — router | Support Triage |
| Workflow — condition | Support Triage |
| Scheduling (cron) | Morning Brief, AI Research, Scheduler |
| Parallel execution | Morning Brief, AI Research, Content Pipeline |
| Cross-modal chaining | Repo Walkthrough |

## Deploy to Railway

Requires:
- [Railway CLI](https://docs.railway.com/guides/cli)
- `OPENAI_API_KEY` set in your environment

```sh
railway login

./scripts/railway_up.sh
```

The script provisions PostgreSQL, configures environment variables, and deploys the application.

### Connect the Web UI

1. Open [os.agno.com](https://os.agno.com)
2. Click "Add OS" -> "Live"
3. Enter your Railway domain

### Manage deployment

```sh
railway logs --service agno-demo      # View logs
railway open                         # Open dashboard
railway up --service agno-demo -d    # Update after changes
```

To stop services:
```sh
railway down --service agno-demo
railway down --service pgvector
```

### Load data in production

```sh
# Dash — table schemas, validated queries, and business rules
railway run python -m agents.dash.scripts.load_knowledge

# Dash — SaaS data (customers, subscriptions, invoices, usage, support)
railway run python -m agents.dash.scripts.load_data
```

## Common Tasks

<details>
<summary><strong>Add your own agent</strong></summary>

1. Create `agents/my_agent/` with these files:

**`agents/my_agent/agent.py`**
```python
from agno.agent import Agent

from agents.my_agent.instructions import INSTRUCTIONS
from app.settings import MODEL, agent_db

my_agent = Agent(
    id="my-agent",
    name="My Agent",
    model=MODEL,
    db=agent_db,
    instructions=INSTRUCTIONS,
    enable_agentic_memory=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
```

**`agents/my_agent/instructions.py`**
```python
INSTRUCTIONS = """\
You are a helpful assistant.
"""
```

**`agents/my_agent/__init__.py`**
```python
from agents.my_agent.agent import my_agent as my_agent
```

**`agents/my_agent/__main__.py`**
```python
from agents.my_agent.agent import my_agent

if __name__ == "__main__":
    my_agent.cli_app(stream=True)
```

2. Register in `app/main.py`:

```python
from agents.my_agent import my_agent

agent_os = AgentOS(
    agents=[..., my_agent],
    ...
)
```

3. Add quick prompts to `app/config.yaml` using the agent's `id`

4. Restart: `docker compose restart`

</details>

<details>
<summary><strong>Add tools to an agent</strong></summary>

Agno includes 100+ tool integrations. See the [full list](https://docs.agno.com/tools/toolkits).

```python
from agno.tools.slack import SlackTools
from agno.tools.scheduler import SchedulerTools

my_agent = Agent(
    ...
    tools=[
        SlackTools(),
        SchedulerTools(db=agent_db),
    ],
)
```

</details>

<details>
<summary><strong>Use a different model provider</strong></summary>

1. Add your API key to `.env` (e.g., `ANTHROPIC_API_KEY`)
2. Update agents to use the new provider:

```python
from agno.models.anthropic import Claude

model=Claude(id="claude-sonnet-4-5")
```
3. Add dependency: `anthropic` in `pyproject.toml`

</details>

<details>
<summary><strong>Connect to Slack</strong></summary>

Slack gives AgentOS two capabilities: receiving messages (DMs, @mentions, threads) and sending messages (proactive posts from Pal, Dash). Each thread maps to a session ID for conversation context.

1. Get a public URL (ngrok for local, deployed URL for production)
2. Create a Slack app from the manifest in the setup guide
3. Install to your workspace
4. Add `SLACK_TOKEN` and `SLACK_SIGNING_SECRET` to `.env`
5. Restart: `docker compose up -d --build`

See [docs/SLACK_CONNECT.md](docs/SLACK_CONNECT.md) for the full setup guide with the app manifest.

</details>

## Local Development

For development without Docker:

```sh
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup environment
./scripts/venv_setup.sh
source .venv/bin/activate

# Start PostgreSQL (required)
docker compose up -d agno-demo-db

# Run the app
python -m app.main
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key (GPT-5.4) |
| `GOOGLE_API_KEY` | No | - | Gemini models for Investment Team |
| `EXA_API_KEY` | No | - | Web search for Reasoner, Reporter, Contacts, Research, Investment |
| `PARALLEL_API_KEY` | No | - | Parallel web search (Pal Researcher) |
| `ELEVENLABS_API_KEY` | No | - | TTS for Studio, Repo Walkthrough |
| `FAL_KEY` | No | - | Image-to-image for Studio |
| `LUMAAI_API_KEY` | No | - | Video generation for Studio |
| `ANTHROPIC_API_KEY` | No | - | Fallback model for Reasoner |
| `SLACK_TOKEN` | No | - | Slack interface + team leader tools ([setup guide](docs/SLACK_CONNECT.md)) |
| `SLACK_SIGNING_SECRET` | No | - | Slack webhook verification ([setup guide](docs/SLACK_CONNECT.md)) |
| `RUNTIME_ENV` | No | `prd` | Set to `dev` for auto-reload |
| `DB_HOST` | No | `localhost` | Database host |
| `DB_PORT` | No | `5432` | Database port |
| `DB_USER` | No | `ai` | Database user |
| `DB_PASS` | No | `ai` | Database password |
| `DB_DATABASE` | No | `ai` | Database name |

## Evals

The eval framework tests all 30 entities across multiple dimensions: basic functionality, tool call correctness, secret leakage, response quality, and latency.

```sh
# Smoke tests (fast, free)
python -m evals smoke                          # All entities
python -m evals smoke --group agents           # By group
python -m evals smoke --entity docs       # Single entity

# Tool call validation (fast, free)
python -m evals reliability

# LLM-judged evals (uses GPT-5.4 as judge)
python -m evals                                # All categories
python -m evals --category accuracy            # Single category

# Performance baselines
python -m evals perf --update-baselines        # Establish baselines
python -m evals perf                           # Compare against baselines

# Improvement loop
python -m evals improve --entity docs     # Debug a failing entity
python -m evals improve --failures             # Debug all failures
```

See [docs/EVALS.md](docs/EVALS.md) for the full eval system documentation.

## Documentation

| Document | What it covers |
|----------|---------------|
| [docs/EVALS.md](docs/EVALS.md) | Eval framework -- smoke tests, reliability, accuracy, performance, improvement loop |
| [docs/SLACK_CONNECT.md](docs/SLACK_CONNECT.md) | Connecting AgentOS to Slack -- app manifest, scopes, credentials |

## Learn More

- [Agno Documentation](https://docs.agno.com)
- [AgentOS Documentation](https://docs.agno.com/agent-os/introduction)
- [Agno Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook)

<p align="center">Built on <a href="https://github.com/agno-agi/agno">Agno</a> · the runtime for agentic software</p>
