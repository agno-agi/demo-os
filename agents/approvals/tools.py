"""
Approvals - Policy-gated tools.

Demonstrates Agno's approval patterns with realistic, policy-driven gating:
1. requires_confirmation (blocking)  - Sensitive operations requiring explicit approval
2. requires_confirmation (audit)     - Audit-trailed operations with confirmation + logging

Each tool runs a policy check that determines WHICH approval level applies based on
amount or risk (auto / manager / VP / CFO / compliance), so the gate reflects real
escalation rules rather than blanket-approving everything. All tools return simulated
responses for demo purposes.
"""

from typing import Literal

from agno.approval import approval
from agno.tools import tool

ReportType = Literal["revenue", "refunds", "churn", "compliance"]

# ---------------------------------------------------------------------------
# Approval policy
# ---------------------------------------------------------------------------
# Refund approval ladder — (exclusive upper bound in USD, approval level).
# A refund is escalated to the first tier whose bound it falls under.
REFUND_LADDER = [
    (100.0, "auto-approve"),
    (1_000.0, "manager"),
    (10_000.0, "VP"),
    (float("inf"), "CFO"),
]


def _refund_level(amount: float) -> tuple[str, str]:
    """Return (approval_level, rationale) for a refund amount.

    Rationale text uses 'USD' rather than a '$' prefix so the UI's Markdown renderer
    never treats a pair of dollar signs as a LaTeX math block.
    """
    for bound, level in REFUND_LADDER:
        if amount < bound:
            if level == "auto-approve":
                return level, f"USD {amount:,.2f} is under the USD 100 auto-approval limit"
            return level, f"USD {amount:,.2f} requires {level}-level sign-off per the refund policy"
    return "CFO", f"USD {amount:,.2f} exceeds all standard limits"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@approval  # type: ignore[call-overload]
@tool(requires_confirmation=True)
def process_refund(customer_id: str, amount: float, reason: str) -> str:
    """Process a customer refund. Approval level is set by policy based on the amount.

    Args:
        customer_id: Customer identifier (e.g. 'C-1042').
        amount: Refund amount in USD.
        reason: Reason for the refund.

    Returns:
        Confirmation with the policy decision and a refund reference number.
    """
    level, rationale = _refund_level(amount)
    ref = f"REF-{abs(hash(customer_id + str(amount))) % 100000:05d}"
    approver = "auto-approved (no sign-off needed)" if level == "auto-approve" else f"{level} approval"
    return (
        f"Refund processed:\n"
        f"  Reference: {ref}\n"
        f"  Customer: {customer_id}\n"
        f"  Amount: USD {amount:,.2f}\n"
        f"  Reason: {reason}\n"
        f"  Policy: {rationale}\n"
        f"  Approval: {approver}\n"
        f"  Status: Approved and queued for next payment cycle"
    )


@approval  # type: ignore[call-overload]
@tool(requires_confirmation=True)
def delete_user_account(user_id: str) -> str:
    """Permanently delete a user account. Always compliance-gated — deletion is irreversible.

    Args:
        user_id: User identifier (e.g. 'U-7788').

    Returns:
        Confirmation of account deletion with the policy decision.
    """
    return (
        f"Account deletion completed:\n"
        f"  User: {user_id}\n"
        f"  Policy: irreversible data deletion — always requires compliance approval\n"
        f"  Approval: compliance sign-off\n"
        f"  Data purged: personal info, payment history, session data\n"
        f"  Retention: anonymized analytics retained per policy\n"
        f"  Confirmation sent to user's email on file"
    )


@approval(type="audit")
@tool(requires_confirmation=True)
def export_customer_data(customer_id: str) -> str:
    """Export all data for a customer (GDPR/CCPA request). Approval + audit-trailed.

    Args:
        customer_id: Customer identifier (e.g. 'C-3021').

    Returns:
        Export status with the policy decision and a download link.
    """
    return (
        f"Data export completed:\n"
        f"  Customer: {customer_id}\n"
        f"  Policy: GDPR/CCPA subject-access export — requires data-protection (DPO) approval\n"
        f"  Approval: DPO sign-off\n"
        f"  Records exported: profile, orders, support tickets, preferences\n"
        f"  Format: JSON archive\n"
        f"  Download: https://internal.example.com/exports/{customer_id}.zip\n"
        f"  Audit log entry created"
    )


@approval(type="audit")
@tool(requires_confirmation=True)
def generate_report(report_type: ReportType, period: str) -> str:
    """Generate a compliance or financial report. Approval + audit-trailed.

    Compliance reports require a higher approval level than routine financial reports.

    Args:
        report_type: One of 'revenue', 'refunds', 'churn', 'compliance'.
        period: Time period (e.g. 'Q4 2025', 'January 2026', '2025').

    Returns:
        Report generation status with the policy decision and a download link.
    """
    if report_type == "compliance":
        policy = "compliance report — requires compliance-officer approval"
        approver = "compliance officer"
    else:
        policy = f"routine {report_type} report — requires finance-manager approval"
        approver = "finance manager"
    return (
        f"Report generated:\n"
        f"  Type: {report_type}\n"
        f"  Period: {period}\n"
        f"  Policy: {policy}\n"
        f"  Approval: {approver}\n"
        f"  Format: PDF + CSV\n"
        f"  Download: https://internal.example.com/reports/{report_type}-{period.replace(' ', '-').lower()}.pdf\n"
        f"  Audit log entry created"
    )
