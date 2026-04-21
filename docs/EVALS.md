# Evaluations

The eval framework tests all 30 AgentOS entities (14 agents, 11 teams, 5 workflows) across multiple dimensions: basic functionality, tool call correctness, secret leakage, response quality, and latency.

Everything runs against the live HTTP API — no mocks, no in-process shortcuts. The server must be running (`docker compose up -d`) before you run evals.

## Architecture

Four eval layers, each catching different failure modes:

```
Layer             Cost    Speed     What it catches
---------------------------------------------------------------------------
Smoke tests       Free    Fast      Crashes, missing keywords, secret leaks,
                                    HITL flow breakage, latency regressions

Reliability       Free    Fast      Wrong tool called, missing tool calls,
                                    broken routing in teams

LLM-Judged        $$      Slow      Bad output quality, inaccurate answers,
                                    vague or incomplete responses

Performance       Free    Medium    Latency regressions across all entities
```

Smoke and reliability tests are pattern-matching — no LLM calls, no cost. Run them constantly. LLM-judged evals use GPT-5.4 as the judge model and cost real money. Run them nightly or before releases. Performance tests hit each entity multiple times and compare against saved baselines.

## Quick Start

```bash
# Start the server
docker compose up -d

# Run the fast tests
python -m evals smoke

# See what failed and why
python -m evals smoke --verbose

# Save results for later comparison
python -m evals smoke --output

# Compare against the last saved run (spot regressions)
python -m evals smoke --output --compare
```

## Smoke Tests

Pattern-matching assertions against live API responses. Each test sends a prompt, then checks:

- **response_contains** — case-insensitive substrings that MUST appear
- **response_not_contains** — substrings that MUST NOT appear (secret patterns, tracebacks)
- **response_matches** — regex patterns
- **max_duration** — latency gate in seconds

Tests are organized into groups:

| Group | Tests | What it covers |
|-------|------:|----------------|
| `agents` | 24 | One or more tests per agent — happy path, edge cases, tool routing |
| `teams` | 12 | Team behavior, mode differentiation (coordinate vs route vs broadcast vs tasks) |
| `workflows` | 6 | End-to-end workflow execution (morning brief, content pipeline, support triage, etc.) |
| `security` | 60 | Secret leakage checks — 21 patterns across representative entities + spot checks |
| `hitl` | 6 | HITL pause/resume — verifies agents pause with the correct tool (restart_service, ask_user, process_refund, etc.) |
| `graceful` | 3 | Graceful degradation when optional API keys are missing |

```bash
python -m evals smoke                          # All groups
python -m evals smoke --group agents           # Just agents
python -m evals smoke --group hitl             # Just HITL tests
python -m evals smoke --group security         # Just security
python -m evals smoke --entity knowledge       # Single entity
python -m evals smoke --verbose                # Show full responses
```

### Security Sampling

Instead of testing every prompt against every entity (which would be 30 x 7 = 210 tests), security uses a sampling strategy:

- **4 representative entities** (helpdesk, reporter, dash, content-pipeline) get all 7 security prompts — these have the highest tool/data surface area
- **All other entities** get 1 spot-check prompt

This gives 60 tests with the same coverage confidence, running in a fraction of the time.

### Adding a Smoke Test

Edit the appropriate file in `evals/cases/smoke/`:

```python
# evals/cases/smoke/agents.py
SmokeTest(
    id="a.15",                                # Unique ID
    name="my-agent — what it tests",          # Human-readable name
    entity_type="agent",                      # "agent" | "team" | "workflow"
    entity_id="my-agent",                     # Must match the registered ID
    group="agents",                           # Determines which --group filter includes it
    prompt="The prompt to send",
    response_contains=["expected", "terms"],   # Case-insensitive substring checks
    response_not_contains=["Traceback"],       # Forbidden patterns
    response_matches=[r"(?i)\bregex\b"],       # Regex patterns
    requires=["SOME_API_KEY"],                 # Skip if env var missing
    max_duration=30.0,                         # Fail if slower than this
)
```

## Reliability Tests

Validates that agents call the correct tools. The HTTP client parses `ToolCallStarted` events from the SSE stream and compares actual tool names against expected ones.

```bash
python -m evals reliability                    # All cases
python -m evals reliability --entity helpdesk  # Single entity
python -m evals reliability --verbose          # Show expected vs actual tools
```

Currently covers: helpdesk (3 tools), approvals (3 tools), scheduler, taskboard, injector.

### Adding a Reliability Case

```python
# evals/cases/reliability.py
{
    "entity_type": "agent",
    "entity_id": "my-agent",
    "input": "Do the thing that calls my_tool",
    "expected_tools": ["my_tool"],
}
```

## LLM-Judged Evals

Uses Agno's `AgentAsJudgeEval` and `AccuracyEval` with GPT-5.4 as the judge. Three categories:

| Category | Type | Cases | What it checks |
|----------|------|------:|----------------|
| `security` | Binary judge | 7 prompts x 30 entities | Agent never reveals secrets — PASS/FAIL |
| `accuracy` | AccuracyEval (1-10) | 13 | Output matches expected answer — pass if score >= 7 |
| `quality` | Numeric judge (1-10) | 6 | Completeness, structure, actionability, conciseness |

```bash
python -m evals                                # All categories
python -m evals --category security            # Just security
python -m evals --category accuracy            # Just accuracy
python -m evals --category quality             # Just quality
python -m evals --verbose                      # Show judge reasoning
```

### Adding an Accuracy Case

```python
# evals/cases/accuracy/agents.py
{
    "entity_type": "agent",
    "entity_id": "knowledge",
    "input": "What is hybrid search in Agno?",
    "expected_output": "Combines keyword and semantic search using PgVector",
    "guidelines": "Must explain it combines two search approaches.",
}
```

## Performance Tests

Hits each entity multiple times, measures latency, compares against saved baselines.

```bash
# First run: establish baselines from live measurements
python -m evals perf --update-baselines

# Later runs: compare against baselines (fail if p95 > baseline * 1.5)
python -m evals perf

# Single entity, more iterations for accuracy
python -m evals perf --entity knowledge --iterations 10
```

Baselines are saved to `evals/.results/perf_baselines.json`. They are measured, not hardcoded — run `--update-baselines` after infrastructure changes to re-establish them.

## Result Persistence

All test commands support `--output` to save results as timestamped JSON files in `evals/.results/`:

```bash
python -m evals smoke --output                 # Saves smoke_20260411_143022.json
python -m evals reliability --output           # Saves reliability_20260411_143055.json
```

Use `--compare` with smoke tests to detect regressions against the last saved run:

```bash
python -m evals smoke --output --compare
# Output:
# ==================================================
# REGRESSIONS: 2 test(s) that passed before now fail
# ==================================================
#   a.3  PASS -> FAIL  missing: diagnostic
#   t.2  PASS -> FAIL  too slow: 65.2s > 60.0s
```

The `.results/` directory is git-ignored.

## Improvement Loop

When tests fail, the improvement loop collects all the context you need to debug in one shot:

```bash
# See what's broken
python -m evals smoke

# Get full context for a failing entity
python -m evals improve --entity knowledge

# Get context for ALL failing entities
python -m evals improve --failures

# Structured JSON output (for programmatic consumption)
python -m evals improve --entity knowledge --json
```

The output includes:
- Smoke test results for that entity
- The full agent response to the failing prompt
- Docker container logs (tool calls, errors, tracebacks)
- The instruction file contents and path
- The agent definition file contents and path

The typical fix loop:

1. Read the improvement data
2. Edit the instruction file (shown in the output)
3. Wait for uvicorn hot-reload
4. Re-run: `python -m evals smoke --entity {id}`

Instruction files are the primary lever. Avoid changing agent definitions (`agent.py`, `team.py`) unless the problem is structural (wrong tools, missing knowledge base).

## Entity Registry

All 30 entities are registered in `evals/registry.py` — the single source of truth. Every eval module imports from here. Adding a new entity means adding one entry:

```python
# evals/registry.py
"my-agent": Entity(
    id="my-agent",
    type="agent",
    instruction_file="agents/my_agent/instructions.py",
    definition_file="agents/my_agent/agent.py",
    requires=["SOME_API_KEY"],  # optional — env vars needed to run
),
```

The registry is used by:
- Security smoke tests (entity list)
- Security judge evals (entity list)
- Improvement loop (instruction/definition file paths)
- Performance tests (entity iteration)

## File Structure

```
evals/
  __init__.py              # Judge model config, eval category registry
  __main__.py              # CLI (smoke, reliability, perf, improve)
  registry.py              # Entity registry — single source of truth
  client.py                # HTTP client (SSE parsing, tool call extraction)
  smoke.py                 # Smoke test runner
  reliability.py           # Reliability test runner
  performance.py           # Performance baseline runner
  results.py               # Result persistence + regression comparison
  improve.py               # Improvement data collector
  run.py                   # Agno eval runner (AccuracyEval, AgentAsJudgeEval)
  docker.py                # Docker log capture
  IMPROVE.md               # Quick reference for the improvement loop
  .results/                # Saved results (git-ignored)
  cases/
    smoke/
      __init__.py          # SmokeTest dataclass
      agents.py            # 24 agent smoke tests
      teams.py             # 12 team smoke tests
      workflows.py         # 6 workflow smoke tests
      security.py          # 60 security smoke tests (sampled)
      hitl.py              # 6 HITL pause/resume tests
      graceful.py          # 3 graceful degradation tests
    reliability.py         # 11 expected tool call cases
    accuracy/
      __init__.py          # Re-exports all accuracy cases
      agents.py            # 8 agent accuracy cases
      teams.py             # 5 team accuracy cases
    judge/
      __init__.py
      quality.py           # Response quality judge (numeric)
    security.py            # Security judge criteria + prompts
```

## CLI Reference

```bash
# Smoke tests (free, fast)
python -m evals smoke [--group GROUP] [--entity ID] [--verbose] [--output] [--compare]

# Reliability (free, fast)
python -m evals reliability [--entity ID] [--verbose] [--output]

# LLM-judged (costs money)
python -m evals [--category CATEGORY] [--verbose] [--output]

# Performance (free, medium)
python -m evals perf [--entity ID] [--iterations N] [--update-baselines] [--output]

# Improvement loop
python -m evals improve --entity ID [--json]
python -m evals improve --failures [--json]

# Global flags (available on all commands)
--url URL              Override API base URL (default: http://localhost:8000)
--timeout SECONDS      Request timeout (default: 120)
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | At least one failure or error |
