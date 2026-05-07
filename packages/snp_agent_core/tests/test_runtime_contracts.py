"""Tests for runtime request, response, tool, citation, and status contracts."""

import pytest
from pydantic import ValidationError

from snp_agent_core.contracts import (
    AgentRunStatus,
    Citation,
    RuntimeRequest,
    RuntimeResponse,
    ToolCallRecord,
)


def test_runtime_request_accepts_valid_payload() -> None:
    """A valid runtime request preserves routing fields and metadata."""

    request = RuntimeRequest(
        tenant_id="tenant_demo",
        channel="api",
        user_id="user_123",
        thread_id="thread_456",
        message="How do I reset my password?",
        metadata={"locale": "en-US"},
    )

    assert request.tenant_id == "tenant_demo"
    assert request.metadata == {"locale": "en-US"}


def test_runtime_request_rejects_empty_required_strings() -> None:
    """Blank request routing and message fields are invalid."""

    with pytest.raises(ValidationError):
        RuntimeRequest(
            tenant_id="tenant_demo",
            channel=" ",
            user_id="user_123",
            thread_id="thread_456",
            message="How do I reset my password?",
        )


def test_runtime_response_serializes_nested_contracts() -> None:
    """Runtime responses serialize enum values, citations, tool records, and metadata."""

    response = RuntimeResponse(
        thread_id="thread_456",
        status=AgentRunStatus.COMPLETED,
        answer="Use the password reset link in your account settings.",
        citations=[
            Citation(
                source_id="kb-password-reset",
                title="Password reset guide",
                uri="https://example.invalid/kb/password-reset",
                quote="Open account settings and choose reset password.",
            )
        ],
        tool_calls=[
            ToolCallRecord(
                tool="knowledge_base.search",
                status="completed",
                latency_ms=42,
                input_summary="password reset query",
                output_summary="one relevant article",
            )
        ],
        trace_id="trace_789",
        handoff_required=False,
        metadata={"agent_id": "customer_service"},
    )

    assert response.model_dump(mode="json") == {
        "thread_id": "thread_456",
        "status": "completed",
        "answer": "Use the password reset link in your account settings.",
        "citations": [
            {
                "source_id": "kb-password-reset",
                "title": "Password reset guide",
                "uri": "https://example.invalid/kb/password-reset",
                "quote": "Open account settings and choose reset password.",
                "metadata": {},
            }
        ],
        "tool_calls": [
            {
                "tool": "knowledge_base.search",
                "status": "completed",
                "latency_ms": 42,
                "input_summary": "password reset query",
                "output_summary": "one relevant article",
                "error": None,
            }
        ],
        "trace_id": "trace_789",
        "handoff_required": False,
        "metadata": {"agent_id": "customer_service"},
    }


def test_tool_call_record_rejects_negative_latency() -> None:
    """Tool call latency must be non-negative when present."""

    with pytest.raises(ValidationError):
        ToolCallRecord(tool="knowledge_base.search", status="failed", latency_ms=-1)


def test_agent_run_status_values_are_stable() -> None:
    """The run status enum exposes exactly the PR-002 status values."""

    assert [status.value for status in AgentRunStatus] == [
        "completed",
        "failed",
        "interrupted",
        "requires_approval",
        "requires_human",
        "rejected_by_safety",
    ]
