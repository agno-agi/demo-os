"""
Accuracy Eval Cases — Agents
=============================

LLM-judged accuracy cases for agents with verifiable outputs.
Scored 1-10 by AccuracyEval, pass threshold >= 7.0.
"""

CASES: list[dict] = [
    # -------------------------------------------------------------------------
    # MCP — documentation via MCP tools
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "mcp",
        "input": "How do I create a custom tool in Agno?",
        "expected_output": "Tool definition using a Python function or class",
        "guidelines": "Must show how to define a tool function. Code example preferred.",
    },
    {
        "entity_type": "agent",
        "entity_id": "mcp",
        "input": "How do I connect to an MCP server in Agno?",
        "expected_output": "MCP server connection setup with URL configuration",
        "guidelines": "Must mention MCP and show how to configure the server URL or endpoint.",
    },
    {
        "entity_type": "agent",
        "entity_id": "mcp",
        "input": "How do I set up a workflow in Agno?",
        "expected_output": "Workflow class setup with steps or tasks",
        "guidelines": "Must reference the Workflow class. Code example preferred.",
    },
    {
        "entity_type": "agent",
        "entity_id": "mcp",
        "input": "How do I use structured outputs with an Agno agent?",
        "expected_output": "Use response_model parameter with a Pydantic model",
        "guidelines": "Must mention response_model. Pydantic model example preferred.",
    },
    {
        "entity_type": "agent",
        "entity_id": "mcp",
        "input": "What happens if an MCP server is unavailable?",
        "expected_output": "Error handling behavior when MCP server cannot be reached",
        "guidelines": "Must discuss error or failure behavior. Not vague.",
    },
    # -------------------------------------------------------------------------
    # Reporter — structured output
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "reporter",
        "input": "Create a brief comparison of Python and Go as JSON",
        "expected_output": "Valid JSON comparing Python and Go on multiple dimensions",
        "guidelines": "Must contain valid JSON structure. Must compare at least 3 dimensions.",
    },
    # -------------------------------------------------------------------------
    # Reasoner — balanced analysis
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "reasoner",
        "input": "Should a startup use microservices or a monolith?",
        "expected_output": "Balanced analysis covering scalability, complexity, team size, and deployment tradeoffs",
        "guidelines": "Must discuss both approaches. Must include at least 3 tradeoff dimensions. Not one-sided.",
    },
]
