"""
Clinic Team — multi-tenant patient assistant.

Showcases four Agno features in one realistic flow:
- Context Provider     — a `dependencies` callable runs live SQL on the operational clinic DB
                         and injects the patient's appointment snapshot into the prompt
- Knowledge Filtering  — clinical documents are retrieved scoped to the current patient_id
                         (the filter is a privacy boundary, not just relevance)
- Followups            — the team suggests sensible next questions after each answer
- Fallback Models      — if the primary model errors, the team falls back across providers
"""

from os import getenv
from typing import Any

from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.team import Team, TeamMode

from app.settings import MODEL, agent_db
from teams.clinic.context import get_patient_context
from teams.clinic.instructions import (
    RECORDS_INSTRUCTIONS,
    SCHEDULER_INSTRUCTIONS,
    TEAM_INSTRUCTIONS,
)
from teams.clinic.knowledge import clinic_knowledge
from teams.clinic.patients import patient_id_for
from teams.clinic.tools import check_formulary, check_provider_availability, list_my_appointments


# ---------------------------------------------------------------------------
# Context provider dependencies (resolved at runtime, injected into context)
# ---------------------------------------------------------------------------
def current_patient_id(run_context: Any) -> str:
    """Resolve the current patient id from the run's user_id (scopes the knowledge filter)."""
    return patient_id_for(getattr(run_context, "user_id", None))


_dependencies = {
    "patient_appointments": get_patient_context,  # live DB query
    "current_patient_id": current_patient_id,  # scopes records retrieval
}

# Fallback chain: if the primary model errors, retry on these in order. A patient
# assistant should stay up, so we fall back across providers when their keys are set.
_fallbacks: list = [OpenAIResponses(id="gpt-5.4-mini")]
if getenv("ANTHROPIC_API_KEY"):
    from agno.models.anthropic import Claude

    _fallbacks.append(Claude(id="claude-sonnet-4-6"))
if getenv("GOOGLE_API_KEY"):
    from agno.models.google import Gemini

    _fallbacks.append(Gemini(id="gemini-3-flash-preview"))

# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------
scheduler = Agent(
    id="clinic-scheduler",
    name="Scheduling Coordinator",
    role="Appointments, provider availability, and formulary coverage from the live clinic DB",
    model=MODEL,
    db=agent_db,
    tools=[list_my_appointments, check_provider_availability, check_formulary],
    instructions=SCHEDULER_INSTRUCTIONS,
    dependencies=_dependencies,
    add_dependencies_to_context=True,
    add_datetime_to_context=True,
    markdown=True,
)

records = Agent(
    id="clinic-records",
    name="Medical Records Specialist",
    role="Patient bloodwork, visit notes, and care plans via patient-scoped record search",
    model=MODEL,
    db=agent_db,
    knowledge=clinic_knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
    instructions=RECORDS_INSTRUCTIONS,
    dependencies=_dependencies,
    add_dependencies_to_context=True,
    add_datetime_to_context=True,
    markdown=True,
)

members: list[Agent | Team] = [scheduler, records]

# ---------------------------------------------------------------------------
# Create Team
# ---------------------------------------------------------------------------
clinic = Team(
    id="clinic",
    name="Clinic",
    description="Patient assistant — live clinic schedule with patient-scoped records.",
    mode=TeamMode.coordinate,
    model=MODEL,
    fallback_models=_fallbacks,
    members=members,
    db=agent_db,
    knowledge=clinic_knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
    instructions=TEAM_INSTRUCTIONS,
    dependencies=_dependencies,
    add_dependencies_to_context=True,
    followups=True,
    num_followups=3,
    share_member_interactions=True,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=5,
    markdown=True,
)
