# Auto-Improvement Loop

Use this prompt to run the eval-driven improvement loop for AgentOS agents.

## How It Works

The system mounts source code into Docker (`compose.yaml` mounts `.:/app` with `--reload`). When you edit an instruction file on disk, the container picks up the change automatically — no rebuild needed.

## The Loop

Run these steps:

1. **Find failures**: `python -m evals smoke`
2. **Get context on each failure**: `python -m evals improve --entity {entity_id}`
3. **Read the output** — it contains:
   - Smoke test results for that entity
   - The full agent response
   - Docker container logs (tool calls, errors, tracebacks)
   - The instruction file contents and path
   - The agent definition file contents and path
4. **Analyze the problem**:
   - Does the response match what the smoke test expects?
   - Are there errors or tracebacks in the Docker logs?
   - Are the instructions missing guidance for this type of query?
   - Is the agent misconfigured (wrong tools, missing knowledge)?
5. **Edit the instruction file** at the path shown in the output
6. **Wait a moment** for uvicorn to hot-reload
7. **Verify the fix**: `python -m evals smoke --entity {entity_id}`
8. **Repeat** steps 2-7 for each failing entity until all pass

## Quick Start

```bash
# Fix all failures in one session
python -m evals smoke                          # See what's broken
python -m evals improve --failures             # Get context on all failures at once

# Then for each failing entity:
# 1. Read the improvement data output
# 2. Edit the instruction file
# 3. Verify: python -m evals smoke --entity {id}
```

## What to Change

Instruction files are the primary lever. When fixing a failure:

- **Missing keywords**: Add guidance to the instructions so the agent naturally uses the expected terms
- **Wrong behavior**: Clarify the agent's role, responsibilities, or response format
- **Tracebacks**: Check if the agent definition has wrong tools or missing config — but prefer instruction fixes first
- **Security leaks**: Add explicit "never reveal" rules to the instructions

Avoid changing agent definition files (`agent.py`, `team.py`) unless the problem is structural (wrong tools, missing knowledge base). Instruction changes are cheaper, faster, and don't risk breaking the agent's configuration.

## CLI Reference

### Smoke Tests (fast, no LLM cost)

```bash
python -m evals smoke                          # All entities
python -m evals smoke --group agents           # Only agents
python -m evals smoke --group teams            # Only teams
python -m evals smoke --group workflows        # Only workflows
python -m evals smoke --group security         # Security pattern checks
python -m evals smoke --group hitl             # HITL pause/resume checks
python -m evals smoke --group graceful         # Graceful degradation
python -m evals smoke --entity knowledge       # Single entity
python -m evals smoke --verbose                # Show full responses
python -m evals smoke --output                 # Save results to evals/.results/
python -m evals smoke --output --compare       # Save + compare to last run
```

### Reliability Tests (tool call validation)

```bash
python -m evals reliability                    # All cases
python -m evals reliability --entity voyager     # Single entity
python -m evals reliability --verbose          # Show expected vs actual tools
```

### Performance Tests (latency baselines)

```bash
python -m evals perf --update-baselines        # Establish baselines from live runs
python -m evals perf                           # Compare against saved baselines
python -m evals perf --entity knowledge        # Single entity
python -m evals perf --iterations 5            # More samples for accuracy
```

### Agno Evals (LLM-judged)

```bash
python -m evals                                # All categories
python -m evals --category security            # Security judge
python -m evals --category accuracy            # Accuracy judge
python -m evals --category quality             # Quality judge
python -m evals --verbose                      # Show judge reasoning
```

### Improvement Data

```bash
python -m evals improve --entity knowledge     # Single entity context
python -m evals improve --failures             # All failing entities
python -m evals improve --entity dash --json   # Structured JSON output
```

## CI Integration

The eval system is designed for tiered CI usage:

| Tier | Trigger | Command | Time Budget |
|------|---------|---------|-------------|
| Smoke | Every push | `python -m evals smoke --output` | < 5 min |
| Reliability | PR to main | `python -m evals reliability` | < 10 min |
| LLM-Judged | Nightly | `python -m evals` | < 30 min |
| Performance | Weekly | `python -m evals perf` | < 15 min |

CI requires: Docker Compose (for the API server), PostgreSQL, and relevant API keys.
