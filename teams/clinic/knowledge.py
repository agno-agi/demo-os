"""
Clinic - Patient-scoped knowledge base (the clinical-documents side).

Patient documents (bloodwork results, visit notes, care plans) are stored in a vector
KB, each tagged with a ``patient_id`` in metadata. The team retrieves with
``knowledge_filters={"patient_id": ...}`` so a patient only ever sees THEIR OWN records —
the filter is the privacy boundary, not just a relevance tweak.
"""

from db import create_knowledge

# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------
clinic_knowledge = create_knowledge("Clinic Records", "clinic_records")

# ---------------------------------------------------------------------------
# Demo patient documents — (patient_id, doc_type, text)
# ---------------------------------------------------------------------------
PATIENT_DOCS: list[tuple[str, str, str]] = [
    (
        "P-1001",
        "bloodwork",
        "Bloodwork for P-1001 (2026-06-01): Cholesterol total 210 mg/dL (borderline high), "
        "LDL 140 (high), HDL 45, fasting glucose 98 (normal), A1C 5.4% (normal). "
        "Recommendation: dietary changes, recheck lipids in 3 months.",
    ),
    (
        "P-1001",
        "visit_note",
        "Visit note for P-1001 (2026-05-20, Dr. Lee): Patient reports mild fatigue. BP 128/82. "
        "Discussed lipid panel results and lifestyle modification. No medication started.",
    ),
    (
        "P-1002",
        "bloodwork",
        "Bloodwork for P-1002 (2026-06-05): Lipid panel within range, LDL 95. "
        "Troponin negative. BNP normal. ECG shows normal sinus rhythm. "
        "Cardiology follow-up scheduled to review exercise tolerance.",
    ),
    (
        "P-1002",
        "care_plan",
        "Care plan for P-1002: Continue Atorvastatin 20mg nightly. Cardiac rehab 2x/week. "
        "Target BP under 130/80. Follow up with Dr. Patel in 4 weeks.",
    ),
    (
        "P-1003",
        "bloodwork",
        "Bloodwork for P-1003 (2026-06-10): A1C 7.8% (elevated), fasting glucose 156 (high), "
        "TSH 4.9 (borderline). Recommendation: start Metformin, endocrinology consult.",
    ),
    (
        "P-1003",
        "care_plan",
        "Care plan for P-1003: Initiate Metformin 500mg with dinner, titrate as tolerated. "
        "Glucose log daily. Thyroid consult with Dr. Gomez. Recheck A1C in 3 months.",
    ),
]
