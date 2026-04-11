"""
Accuracy Eval Cases — Agents
=============================

LLM-judged accuracy cases for agents with verifiable outputs.
Scored 1-10 by AccuracyEval, pass threshold >= 7.0.
"""

CASES: list[dict] = [
    # -------------------------------------------------------------------------
    # Docs — documentation retrieval
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "docs",
        "input": "What model providers does Agno support?",
        "expected_output": "OpenAI, Anthropic, Google/Gemini among supported providers",
        "guidelines": "Must name at least 3 specific providers.",
    },
    {
        "entity_type": "agent",
        "entity_id": "docs",
        "input": "How do you create a knowledge base in Agno?",
        "expected_output": "Use the Knowledge class with a vector database like PgVector",
        "guidelines": "Must mention Knowledge class and vector database. Code example preferred.",
    },
    {
        "entity_type": "agent",
        "entity_id": "docs",
        "input": "What is hybrid search in Agno?",
        "expected_output": "Combines keyword and semantic search using PgVector SearchType.hybrid",
        "guidelines": "Must explain it combines two search approaches. Mention PgVector if possible.",
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
    # Scheduler — operations
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "scheduler",
        "input": "List all active schedules",
        "expected_output": "List of scheduled tasks with their cron patterns and status",
        "guidelines": "Must show schedule details or clearly state none exist. Not vague.",
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
    # -------------------------------------------------------------------------
    # Injector — config accuracy
    # -------------------------------------------------------------------------
    {
        "entity_type": "agent",
        "entity_id": "injector",
        "input": "What is the app name and version?",
        "expected_output": "AgentOS Demo version 2.1.0",
        "guidelines": "Must state the exact app name and version number from the config.",
    },
    {
        "entity_type": "agent",
        "entity_id": "injector",
        "input": "Which features are currently disabled?",
        "expected_output": "beta_features, multi_language, real_time_collaboration are disabled",
        "guidelines": "Must correctly list the disabled feature flags. Must not include enabled features.",
    },
]
