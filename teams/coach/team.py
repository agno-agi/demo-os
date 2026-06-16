"""Coach Team (Mentor) — a learning-focused assistant that improves over time.

This team is the showcase for Agno's LearningMachine. Where
other teams use a single learning store, Mentor turns on five at once so the team
visibly gets better — and more personalized — the more it works with the user:

- ``user_profile``      — who the user is (role, goals, stack)
- ``user_memory``       — durable preferences and facts
- ``session_context``   — the current task/goal within this conversation
- ``learned_knowledge`` — reusable lessons and playbooks distilled across sessions
- ``decision_log``      — decisions made, with their rationale

The Coach delivers tailored guidance; the Curator keeps the memory clean.
Followups are enabled here because the suggested next
questions are grounded in accumulated learnings, so they stay answerable and get
richer the longer the conversation runs.
"""

from typing import Any  # noqa: UP035 — used for dict[str, Any] unpacking

from agno.agent import Agent
from agno.learn import (
    DecisionLogConfig,
    LearnedKnowledgeConfig,
    LearningMachine,
    LearningMode,
    SessionContextConfig,
    UserMemoryConfig,
    UserProfileConfig,
)
from agno.team import Team, TeamMode

from app.settings import MODEL, agent_db
from db import create_knowledge
from teams.coach.instructions import (
    COACH_INSTRUCTIONS,
    COORDINATE_INSTRUCTIONS,
    CURATOR_INSTRUCTIONS,
)

# ---------------------------------------------------------------------------
# Shared settings
# ---------------------------------------------------------------------------
coach_learnings = create_knowledge("Coach Learnings", "coach_learnings")

# A LearningMachine with five stores enabled. learned_knowledge is AGENTIC (the
# model decides when a reusable lesson is worth keeping); profile, memories,
# session context, and the decision log run ALWAYS so signal is captured as it
# appears. session_context tracks the *here-and-now* of the active conversation
# (the current task/goal), complementing the cross-session stores.
_learning = LearningMachine(
    db=agent_db,
    knowledge=coach_learnings,
    user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
    user_memory=UserMemoryConfig(mode=LearningMode.ALWAYS),
    session_context=SessionContextConfig(mode=LearningMode.ALWAYS),
    learned_knowledge=LearnedKnowledgeConfig(
        mode=LearningMode.AGENTIC,
        namespace="global",
    ),
    decision_log=DecisionLogConfig(mode=LearningMode.ALWAYS),
)

_common: dict[str, Any] = dict(
    db=agent_db,
    learning=_learning,
    add_learnings_to_context=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------
coach = Agent(
    id="coach-mentor",
    name="Mentor",
    role="Tailored coaching and onboarding grounded in what's already learned",
    model=MODEL,
    instructions=COACH_INSTRUCTIONS,
    **_common,
)

curator = Agent(
    id="coach-curator",
    name="Curator",
    role="Extracts and maintains durable learnings — memories, lessons, decisions",
    model=MODEL,
    instructions=CURATOR_INSTRUCTIONS,
    **_common,
)

members: list[Agent | Team] = [coach, curator]

# ---------------------------------------------------------------------------
# Create Team (coordinate mode)
# ---------------------------------------------------------------------------
coach_team = Team(
    id="mentor",
    name="Mentor",
    description="Learning-focused coach that gets better at helping you over time, powered by the LearningMachine.",
    mode=TeamMode.coordinate,
    model=MODEL,
    members=members,
    db=agent_db,
    learning=_learning,
    add_learnings_to_context=True,
    instructions=COORDINATE_INSTRUCTIONS,
    followups=True,
    num_followups=3,
    share_member_interactions=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
