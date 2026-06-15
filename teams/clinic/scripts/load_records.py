"""
Load Clinic Records
===================

Loads patient documents into the vector knowledge base, each tagged with a
``patient_id`` in metadata so the team can filter retrieval per patient.

Usage:
    python -m teams.clinic.scripts.load_records             # Upsert
    python -m teams.clinic.scripts.load_records --recreate  # Drop + reload
"""

import argparse

from teams.clinic.knowledge import PATIENT_DOCS, clinic_knowledge

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load patient records into the knowledge base")
    parser.add_argument("--recreate", action="store_true", help="Drop existing records and reload")
    args = parser.parse_args()

    if args.recreate and clinic_knowledge.vector_db:
        print("Recreating clinic records (dropping existing data)...")
        clinic_knowledge.vector_db.drop()
        clinic_knowledge.vector_db.create()

    print(f"Loading {len(PATIENT_DOCS)} patient documents...")
    for patient_id, doc_type, text in PATIENT_DOCS:
        clinic_knowledge.insert(
            name=f"{patient_id}-{doc_type}",
            text_content=text,
            metadata={"patient_id": patient_id, "doc_type": doc_type},
        )
        print(f"  + {patient_id} / {doc_type}")

    print("Done.")
