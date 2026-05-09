"""Typed state sketch for the current chatbot demo reference agent."""

from __future__ import annotations

from typing import TypedDict


class CurrentChatbotDemoState(TypedDict, total=False):
    """State fields expected by the future customer-service graph."""

    tenant_id: str
    user_id: str
    channel: str
    thread_id: str
    request_id: str
    message: str
    intent: str
    safety_decision: str
    retrieval_query: str
    tool_name: str
    answer: str

