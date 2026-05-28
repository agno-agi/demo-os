"""
Dash Team
=========

A self-learning data agent that provides insights, not just query results.
The leader routes requests to specialized agents:
Analyst for SQL/data queries, Engineer for schema/pipeline operations.
"""

from agno.team import Team, TeamMode

from agents.dash.agents.analyst import analyst
from agents.dash.agents.engineer import engineer
from agents.dash.instructions import build_leader_instructions
from agents.dash.settings import MODEL, SLACK_TOKEN, agent_db, dash_learning

# ---------------------------------------------------------------------------
# Team Leader Tools (Slack — leader-only)
# ---------------------------------------------------------------------------
leader_tools: list = []
if SLACK_TOKEN:
    from agno.tools.slack import SlackTools

    leader_tools.append(
        SlackTools(
            enable_send_message=True,
            enable_list_channels=True,
            enable_send_message_thread=True,
            enable_get_channel_info=True,
            enable_get_thread=True,
            enable_get_user_info=True,
            enable_search_messages=True,
        )
    )

# ---------------------------------------------------------------------------
# Create Team
# ---------------------------------------------------------------------------
dash = Team(
    id="dash",
    name="Dash",
    mode=TeamMode.coordinate,
    model=MODEL,
    members=[analyst, engineer],
    db=agent_db,
    tools=leader_tools,
    # Leader only needs learnings for context (error patterns, gotchas).
    # Curated knowledge (SQL, table metadata) is for the specialists.
    learning=dash_learning,
    add_learnings_to_context=True,
    instructions=build_leader_instructions(),
    # Member coordination
    share_member_interactions=True,
    # Memory
    enable_agentic_memory=True,
    search_past_sessions=True,
    num_past_sessions_to_search=5,
    # Context
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Run Team
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        "Hey, what can you do?",
        "What's our current MRR?",
        "Which plan has the highest churn rate?",
        "Show me the schema for the customers table",
        "Create a view for monthly MRR by plan",
    ]
    for idx, prompt in enumerate(test_cases, start=1):
        print(f"\n--- Dash test case {idx}/{len(test_cases)} ---")
        print(f"Prompt: {prompt}")
        dash.print_response(prompt, stream=True)
