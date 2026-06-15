"""
Clinic - Operational DB tools (the live, structured side).

These tools run real read-only SQL against the seeded `clinic.*` tables so the
Scheduling agent can answer operational questions ("is Dr. Lee free Thursday?",
"what's on the formulary for diabetes?"). They complement the context provider
(which injects the patient's upcoming appointments automatically each turn).
"""

from agno.run import RunContext
from agno.tools import tool
from sqlalchemy import create_engine, text

from db import db_url
from teams.clinic.patients import patient_id_for

_engine = create_engine(db_url, pool_pre_ping=True)

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}


@tool
def list_my_appointments(run_context: RunContext) -> str:
    """List the current patient's appointments (scheduled and past). Scoped to the logged-in patient."""
    patient_id = patient_id_for(getattr(run_context, "user_id", None))
    with _engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT a.appt_date, a.appt_time, p.name, a.reason, a.status "
                "FROM clinic.appointments a JOIN clinic.providers p USING (provider_id) "
                "WHERE a.patient_id = :pid ORDER BY a.appt_date, a.appt_time"
            ),
            {"pid": patient_id},
        ).fetchall()
    if not rows:
        return f"No appointments on file for {patient_id}."
    lines = [f"Appointments for {patient_id}:"]
    for d, t, name, reason, status in rows:
        lines.append(f"- {d} {t} — {name} — {reason} ({status})")
    return "\n".join(lines)


@tool
def check_provider_availability(provider_name: str, weekday: str = "") -> str:
    """Check which days/hours a provider is available, optionally for a specific weekday.

    Args:
        provider_name: Provider name or fragment (e.g. 'Lee', 'Dr. Patel').
        weekday: Optional weekday to check (e.g. 'Thursday'). Leave empty for the full week.
    """
    with _engine.connect() as conn:
        prov = conn.execute(
            text("SELECT provider_id, name, specialty FROM clinic.providers WHERE name ILIKE :q"),
            {"q": f"%{provider_name}%"},
        ).fetchone()
        if prov is None:
            return f"No provider matching '{provider_name}'."
        provider_id, name, specialty = prov

        query = "SELECT weekday, start_time, end_time FROM clinic.availability WHERE provider_id = :pid"
        params: dict = {"pid": provider_id}
        if weekday:
            wd = _WEEKDAYS.get(weekday.strip().lower())
            if wd is None:
                return f"'{weekday}' isn't a clinic weekday (Mon–Fri)."
            query += " AND weekday = :wd"
            params["wd"] = wd
        query += " ORDER BY weekday"
        rows = conn.execute(text(query), params).fetchall()

    if not rows:
        when = f" on {weekday.title()}" if weekday else ""
        return f"{name} ({specialty}) has no availability{when}."
    names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    lines = [f"{name} ({specialty}) availability:"]
    for wd, st, en in rows:
        lines.append(f"- {names[wd]}: {st}–{en}")
    return "\n".join(lines)


@tool
def check_formulary(drug_or_condition: str) -> str:
    """Look up whether a drug is on the clinic formulary (covered), with tier and notes.

    Args:
        drug_or_condition: A drug name or fragment (e.g. 'Metformin', 'statin', 'Ozempic').
    """
    with _engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT drug, form, on_formulary, tier, note FROM clinic.formulary "
                "WHERE drug ILIKE :q OR note ILIKE :q ORDER BY drug"
            ),
            {"q": f"%{drug_or_condition}%"},
        ).fetchall()
    if not rows:
        return f"No formulary entry matching '{drug_or_condition}'."
    lines = ["Formulary results:"]
    for drug, form, on_f, tier, note in rows:
        status = "covered" if on_f else "NOT covered"
        lines.append(f"- {drug} ({form}) — {status}, tier: {tier}. {note}")
    return "\n".join(lines)
