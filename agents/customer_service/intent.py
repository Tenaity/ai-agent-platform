"""Deterministic intent routing for the customer service demo graph.

This module intentionally uses simple local string matching. It is a temporary
runtime boundary before future LLM-based routing exists, which keeps tests
deterministic and avoids model calls.
"""

from enum import StrEnum


class CustomerServiceIntent(StrEnum):
    """Supported deterministic intent buckets for the demo graph."""

    POLICY_QUESTION = "policy_question"
    CONTAINER_TRACKING = "container_tracking"
    BOOKING_STATUS = "booking_status"
    SUPPORT_TICKET = "support_ticket"
    FALLBACK = "fallback"


def classify_intent(message: str) -> CustomerServiceIntent:
    """Classify a message using deterministic keyword rules."""

    lowered = message.casefold()

    if any(term in lowered for term in ("container", "cont", "mã cont", "tracking")):
        return CustomerServiceIntent.CONTAINER_TRACKING
    if "booking" in lowered:
        return CustomerServiceIntent.BOOKING_STATUS
    if any(term in lowered for term in ("quy trình", "giờ làm việc", "phí", "chính sách")):
        return CustomerServiceIntent.POLICY_QUESTION
    if any(term in lowered for term in ("ticket", "hỗ trợ", "khiếu nại")):
        return CustomerServiceIntent.SUPPORT_TICKET
    return CustomerServiceIntent.FALLBACK
