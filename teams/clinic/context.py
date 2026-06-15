"""
Clinic - Context Provider (live operational DB).

A *context provider* is a `dependencies` value that is a callable. Agno resolves it at
runtime (it receives `run_context`, may be async) and — with
`add_dependencies_to_context=True` — injects the result into the model's prompt under an
`<additional context>` block.

Here the provider runs **real SQL** against the operational clinic tables (seeded by
`scripts/seed_clinic.py`) to inject the current patient's upcoming-appointment snapshot
into every turn. This is the live, structured side of the assistant — distinct from the
patient's clinical *documents*, which are retrieved via filtered knowledge search.
"""

from typing import Any

from sqlalchemy import create_engine, text

from db import db_url
from teams.clinic.patients import patient_id_for

# One engine for the module (pooled); the provider issues read-only SELECTs.
_engine = create_engine(db_url, pool_pre_ping=True)


def get_patient_context(run_context: Any) -> str:
    """Context provider — inject the current patient's live appointment snapshot.

    Resolved by Agno at runtime and added to the prompt. Scoped to the patient mapped
    from the run's ``user_id`` so each patient only ever sees their own schedule.
    """
    patient_id = patient_id_for(getattr(run_context, "user_id", None))

    with _engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT a.appt_date, a.appt_time, p.name, p.specialty, a.reason, a.status "
                "FROM clinic.appointments a JOIN clinic.providers p USING (provider_id) "
                "WHERE a.patient_id = :pid AND a.status = 'scheduled' "
                "ORDER BY a.appt_date, a.appt_time"
            ),
            {"pid": patient_id},
        ).fetchall()

    if not rows:
        return f"Patient {patient_id}: no upcoming appointments on file."

    lines = [f"Patient {patient_id} — upcoming appointments:"]
    for appt_date, appt_time, name, specialty, reason, _status in rows:
        lines.append(f"- {appt_date} {appt_time} with {name} ({specialty}) — {reason}")
    return "\n".join(lines)
