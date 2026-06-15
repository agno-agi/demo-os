"""
Seed Clinic Operational Data
============================

Creates the operational tables the Context Provider queries at runtime — providers,
their weekly availability, and patient appointments — for a fictional clinic
("Riverside Family Health"). This is REAL Postgres data, not a mock: the context
provider runs live SQL against these tables.

Usage:
    python -m teams.onboarding.scripts.seed_clinic            # Create + seed
    python -m teams.onboarding.scripts.seed_clinic --drop     # Drop and recreate
"""

import argparse

from sqlalchemy import create_engine, text

from db import db_url

# ---------------------------------------------------------------------------
# Seed data (small, legible, deterministic)
# ---------------------------------------------------------------------------
PROVIDERS = [
    ("DR-LEE", "Dr. Karen Lee", "Family Medicine"),
    ("DR-PATEL", "Dr. Anil Patel", "Cardiology"),
    ("DR-GOMEZ", "Dr. Maria Gomez", "Endocrinology"),
]

# provider_id, weekday (0=Mon .. 4=Fri), start, end
AVAILABILITY = [
    ("DR-LEE", 1, "09:00", "16:00"),  # Tue
    ("DR-LEE", 3, "09:00", "16:00"),  # Thu
    ("DR-PATEL", 0, "08:00", "12:00"),  # Mon
    ("DR-PATEL", 2, "13:00", "17:00"),  # Wed
    ("DR-GOMEZ", 3, "10:00", "15:00"),  # Thu
    ("DR-GOMEZ", 4, "09:00", "13:00"),  # Fri
]

# patient_id, provider_id, date, time, reason, status
APPOINTMENTS = [
    ("P-1001", "DR-LEE", "2026-06-18", "10:30", "Annual physical", "scheduled"),
    ("P-1001", "DR-GOMEZ", "2026-07-02", "11:00", "A1C review", "scheduled"),
    ("P-1002", "DR-PATEL", "2026-06-17", "09:00", "Cardiology follow-up", "scheduled"),
    ("P-1002", "DR-LEE", "2026-05-20", "14:00", "Sick visit", "completed"),
    ("P-1003", "DR-GOMEZ", "2026-06-19", "10:00", "Thyroid consult", "scheduled"),
]

# drug, form, on_formulary, tier, note
FORMULARY = [
    ("Metformin", "500mg tablet", True, "generic", "Preferred first-line for type 2 diabetes"),
    ("Atorvastatin", "20mg tablet", True, "generic", "Preferred statin"),
    ("Lisinopril", "10mg tablet", True, "generic", "Preferred ACE inhibitor"),
    ("Ozempic", "1mg pen", True, "specialty", "Prior authorization required"),
    ("Brand-X", "50mg tablet", False, "non-formulary", "Not covered — use generic equivalent"),
]

DDL = """
CREATE SCHEMA IF NOT EXISTS clinic;

CREATE TABLE IF NOT EXISTS clinic.providers (
    provider_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    specialty   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clinic.availability (
    provider_id TEXT NOT NULL REFERENCES clinic.providers(provider_id),
    weekday     INT  NOT NULL,
    start_time  TEXT NOT NULL,
    end_time    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clinic.appointments (
    id          SERIAL PRIMARY KEY,
    patient_id  TEXT NOT NULL,
    provider_id TEXT NOT NULL REFERENCES clinic.providers(provider_id),
    appt_date   DATE NOT NULL,
    appt_time   TEXT NOT NULL,
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clinic.formulary (
    drug          TEXT PRIMARY KEY,
    form          TEXT NOT NULL,
    on_formulary  BOOLEAN NOT NULL,
    tier          TEXT NOT NULL,
    note          TEXT NOT NULL
);
"""


def main(drop: bool) -> None:
    engine = create_engine(db_url)
    with engine.begin() as conn:
        if drop:
            print("Dropping clinic schema...")
            conn.execute(text("DROP SCHEMA IF EXISTS clinic CASCADE;"))

        for stmt in DDL.strip().split(";\n"):
            if stmt.strip():
                conn.execute(text(stmt))

        # Idempotent seed: clear rows, then insert.
        conn.execute(text("DELETE FROM clinic.appointments;"))
        conn.execute(text("DELETE FROM clinic.availability;"))
        conn.execute(text("DELETE FROM clinic.formulary;"))
        conn.execute(text("DELETE FROM clinic.providers;"))

        for pid, name, spec in PROVIDERS:
            conn.execute(
                text("INSERT INTO clinic.providers (provider_id, name, specialty) VALUES (:p, :n, :s)"),
                {"p": pid, "n": name, "s": spec},
            )
        for pid, wd, st, en in AVAILABILITY:
            conn.execute(
                text(
                    "INSERT INTO clinic.availability (provider_id, weekday, start_time, end_time) "
                    "VALUES (:p, :w, :s, :e)"
                ),
                {"p": pid, "w": wd, "s": st, "e": en},
            )
        for pat, prov, d, t, reason, status in APPOINTMENTS:
            conn.execute(
                text(
                    "INSERT INTO clinic.appointments (patient_id, provider_id, appt_date, appt_time, reason, status) "
                    "VALUES (:pat, :prov, :d, :t, :r, :st)"
                ),
                {"pat": pat, "prov": prov, "d": d, "t": t, "r": reason, "st": status},
            )
        for drug, form, on_f, tier, note in FORMULARY:
            conn.execute(
                text("INSERT INTO clinic.formulary (drug, form, on_formulary, tier, note) VALUES (:d, :f, :o, :t, :n)"),
                {"d": drug, "f": form, "o": on_f, "t": tier, "n": note},
            )

    print(
        f"Seeded clinic: {len(PROVIDERS)} providers, {len(AVAILABILITY)} availability rows, "
        f"{len(APPOINTMENTS)} appointments, {len(FORMULARY)} formulary entries."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed clinic operational data")
    parser.add_argument("--drop", action="store_true", help="Drop and recreate the clinic schema")
    main(parser.parse_args().drop)
