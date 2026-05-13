"""Tests for reusable human-in-the-loop contracts and store."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from snp_agent_core.human_loop import (
    ApprovalNotFoundError,
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalStateError,
    ApprovalStatus,
    InMemoryApprovalStore,
)


def _approval(approval_id: str = "approval-123") -> ApprovalRequest:
    return ApprovalRequest(
        approval_id=approval_id,
        agent_id="customer_service",
        tenant_id="demo",
        user_id="telegram:123456",
        channel="telegram",
        thread_id="telegram:123456",
        action_name="refund_review",
        action_summary="Review refund request before execution.",
        risk_level=ApprovalRiskLevel.HIGH,
        created_at=datetime.now(UTC),
        metadata={"source": "test"},
    )


def test_approval_request_validates() -> None:
    request = _approval()

    assert request.status == ApprovalStatus.PENDING
    assert request.created_at.utcoffset() == UTC.utcoffset(request.created_at)


def test_approval_request_rejects_blank_required_strings() -> None:
    with pytest.raises(ValidationError):
        ApprovalRequest(
            approval_id="approval-123",
            agent_id=" ",
            tenant_id="demo",
            user_id="telegram:123456",
            channel="telegram",
            action_name="refund_review",
            action_summary="Review refund request before execution.",
            risk_level=ApprovalRiskLevel.HIGH,
            created_at=datetime.now(UTC),
        )


def test_approval_request_rejects_naive_created_at() -> None:
    with pytest.raises(ValidationError):
        ApprovalRequest(
            approval_id="approval-123",
            agent_id="customer_service",
            tenant_id="demo",
            user_id="telegram:123456",
            channel="telegram",
            action_name="refund_review",
            action_summary="Review refund request before execution.",
            risk_level=ApprovalRiskLevel.HIGH,
            created_at=datetime(2026, 5, 13, 8, 0, 0),
        )


def test_in_memory_approval_store_create_get_and_list_pending() -> None:
    store = InMemoryApprovalStore()
    request = store.create(_approval())

    assert store.get(request.approval_id) == request
    assert store.list_pending() == [request]


def test_in_memory_approval_store_approve_pending_request() -> None:
    store = InMemoryApprovalStore()
    request = store.create(_approval())

    approved = store.approve(request.approval_id, decided_by="operator")

    assert approved.status == ApprovalStatus.APPROVED
    assert approved.decided_by == "operator"
    assert approved.decided_at is not None
    assert store.list_pending() == []


def test_in_memory_approval_store_reject_pending_request() -> None:
    store = InMemoryApprovalStore()
    request = store.create(_approval())

    rejected = store.reject(request.approval_id, decided_by="operator")

    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.decided_by == "operator"
    assert store.list_pending() == []


def test_in_memory_approval_store_cannot_approve_unknown_id() -> None:
    store = InMemoryApprovalStore()

    with pytest.raises(ApprovalNotFoundError):
        store.approve("missing", decided_by="operator")


def test_in_memory_approval_store_cannot_approve_already_approved_request() -> None:
    store = InMemoryApprovalStore()
    request = store.create(_approval())
    store.approve(request.approval_id, decided_by="operator")

    with pytest.raises(ApprovalStateError):
        store.approve(request.approval_id, decided_by="operator")
