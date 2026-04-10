"""Mock tools for Morning Brief workflow."""

from agno.tools import tool


@tool
def get_todays_calendar() -> str:
    """Get today's calendar events."""
    return """
Today's Calendar:
- 9:00 AM - Standup (15 min) — Team sync, all engineering
- 10:00 AM - Product Review (60 min) — Demo new agent features to PM team. Prep: have demo running.
- 12:00 PM - Lunch with Sarah Chen (Acme Corp CTO) — Discussion: partnership proposal
- 2:00 PM - Architecture Review (45 min) — Review Dash schema migration plan
- 4:00 PM - 1:1 with Manager (30 min) — Q2 goals check-in
"""


@tool
def get_email_digest() -> str:
    """Get today's email digest."""
    return """
Inbox Summary (12 unread):
URGENT:
- [Security] Production alert: Auth service latency spike at 3 AM — resolved by oncall, RCA pending
- [Finance] Q1 board deck review needed by EOD Thursday

ACTION REQUIRED:
- [HR] Benefits enrollment deadline extended to Friday
- [Product] Feature flag review for v2.6 release — approve/reject by Wednesday
- [Legal] Updated contractor agreement needs signature

FYI:
- [Engineering] New hire starting Monday: Alex Kim (Backend)
- [All-hands] Company all-hands moved to next Tuesday 3 PM
- [Product] Customer feedback summary for March
- [IT] Scheduled maintenance window Saturday 2-6 AM
- [Marketing] Blog post draft: "Building with AI Agents" — review optional
- [Engineering] CI/CD pipeline upgrade complete
- [Social] Team lunch Friday at noon
"""
