"""
Approvals - Approval-gated tools.

Demonstrates Agno's approval patterns:
1. requires_confirmation (blocking)  - Sensitive operations requiring explicit approval
2. requires_confirmation (audit)     - Audit-trailed operations with confirmation + logging

All tools return simulated responses for demo purposes.
"""

from typing import Literal

from agno.approval import approval
from agno.tools import tool

ReportType = Literal["revenue", "refunds", "churn", "compliance"]


@approval  # type: ignore[call-overload]
@tool(requires_confirmation=True)
def process_refund(customer_id: str, amount: float, reason: str) -> str:
    """Process a refund for a customer. Requires manager approval before executing.

    Args:
        customer_id: Customer identifier (e.g. 'C-1042').
        amount: Refund amount in USD.
        reason: Reason for the refund.

    Returns:
        Confirmation with refund reference number.
    """
    ref = f"REF-{abs(hash(customer_id + str(amount))) % 100000:05d}"
    return (
        f"Refund processed:\n"
        f"  Reference: {ref}\n"
        f"  Customer: {customer_id}\n"
        f"  Amount: ${amount:.2f}\n"
        f"  Reason: {reason}\n"
        f"  Status: Approved and queued for next payment cycle"
    )


@approval  # type: ignore[call-overload]
@tool(requires_confirmation=True)
def delete_user_account(user_id: str) -> str:
    """Permanently delete a user account. Requires compliance approval before executing.

    Args:
        user_id: User identifier (e.g. 'U-7788').

    Returns:
        Confirmation of account deletion.
    """
    return (
        f"Account deletion completed:\n"
        f"  User: {user_id}\n"
        f"  Data purged: personal info, payment history, session data\n"
        f"  Retention: anonymized analytics retained per policy\n"
        f"  Confirmation sent to user's email on file"
    )


@approval(type="audit")
@tool(requires_confirmation=True)
def export_customer_data(customer_id: str) -> str:
    """Export all data for a customer (GDPR/CCPA request). Requires approval and is logged to audit trail.

    Args:
        customer_id: Customer identifier (e.g. 'C-3021').

    Returns:
        Export status with download link.
    """
    return (
        f"Data export completed:\n"
        f"  Customer: {customer_id}\n"
        f"  Records exported: profile, orders, support tickets, preferences\n"
        f"  Format: JSON archive\n"
        f"  Download: https://internal.example.com/exports/{customer_id}.zip\n"
        f"  Audit log entry created"
    )


@approval(type="audit")
@tool(requires_confirmation=True)
def generate_report(report_type: ReportType, period: str) -> str:
    """Generate a compliance or financial report. Requires approval and is logged to audit trail.

    Args:
        report_type: One of 'revenue', 'refunds', 'churn', 'compliance'.
        period: Time period (e.g. 'Q4 2025', 'January 2026', '2025').

    Returns:
        Report generation status with download link.
    """
    return (
        f"Report generated:\n"
        f"  Type: {report_type}\n"
        f"  Period: {period}\n"
        f"  Format: PDF + CSV\n"
        f"  Download: https://internal.example.com/reports/{report_type}-{period.replace(' ', '-').lower()}.pdf\n"
        f"  Audit log entry created"
    )
