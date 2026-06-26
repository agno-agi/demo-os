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
        "entity_id": "agno-expert",
        "input": "How do I create a custom tool in Agno?",
        "expected_output": "Tool definition using a Python function or class",
        "guidelines": "Must show how to define a tool function. Code example preferred.",
    },
    {
        "entity_type": "agent",
        "entity_id": "agno-expert",
        "input": "How do I connect to an MCP server in Agno?",
        "expected_output": "MCP server connection setup with URL configuration",
        "guidelines": "Must mention MCP and show how to configure the server URL or endpoint.",
    },
    {
        "entity_type": "agent",
        "entity_id": "agno-expert",
        "input": "How do I set up a workflow in Agno?",
        "expected_output": "Workflow class setup with steps or tasks",
        "guidelines": "Must reference the Workflow class. Code example preferred.",
    },
    {
        "entity_type": "agent",
        "entity_id": "agno-expert",
        "input": "How do I use structured outputs with an Agno agent?",
        "expected_output": "Use response_model parameter with a Pydantic model",
        "guidelines": "Must mention response_model. Pydantic model example preferred.",
    },
    {
        "entity_type": "agent",
        "entity_id": "agno-expert",
        "input": "What happens if an MCP server is unavailable?",
        "expected_output": "Error handling behavior when MCP server cannot be reached",
        "guidelines": "Must discuss error or failure behavior. Not vague.",
    },
    # -------------------------------------------------------------------------
    # Reporter — researched, structured report
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "researcher",
        "input": "Write a brief comparison of Python and Go",
        "expected_output": "A structured report comparing Python and Go on multiple dimensions",
        "guidelines": "Must compare at least 3 dimensions with clear structure (headings or sections).",
    },
]
