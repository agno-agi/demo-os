"""
Clinic - Patient identity mapping.

Maps the run's authenticated ``user_id`` to a clinic ``patient_id``. In a real system
this would be a lookup in your identity/patient-MRN service; here it's a small map, and
the demo defaults to a sample patient when no user is set. The resolved patient_id scopes
BOTH the operational DB context provider and the patient-scoped knowledge filter.
"""

# user_id -> patient_id
_USER_TO_PATIENT = {
    "alice": "P-1001",
    "bob": "P-1002",
    "carol": "P-1003",
}

DEFAULT_PATIENT_ID = "P-1002"


def patient_id_for(user_id: str | None) -> str:
    """Resolve the current patient_id from the run's user_id (sample patient by default)."""
    if not user_id:
        return DEFAULT_PATIENT_ID
    # Accept either a known username or a raw patient id passed as user_id.
    if user_id in _USER_TO_PATIENT:
        return _USER_TO_PATIENT[user_id]
    if user_id.startswith("P-"):
        return user_id
    return DEFAULT_PATIENT_ID
