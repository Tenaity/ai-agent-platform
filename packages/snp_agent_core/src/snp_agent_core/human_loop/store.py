"""Human approval store interfaces and local in-memory implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from snp_agent_core.human_loop.contracts import ApprovalRequest, ApprovalStatus


class ApprovalStoreError(RuntimeError):
    """Base error for approval store operations."""


class ApprovalNotFoundError(ApprovalStoreError):
    """Raised when an approval id does not exist."""


class ApprovalStateError(ApprovalStoreError):
    """Raised when a non-pending approval is decided again."""


class ApprovalStore(ABC):
    """Abstract persistence boundary for human approval requests."""

    @abstractmethod
    def create(self, request: ApprovalRequest) -> ApprovalRequest:
        """Create and return an approval request."""

    @abstractmethod
    def get(self, approval_id: str) -> ApprovalRequest:
        """Return an approval request by id."""

    @abstractmethod
    def approve(
        self,
        approval_id: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Approve a pending request."""

    @abstractmethod
    def reject(
        self,
        approval_id: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Reject a pending request."""

    @abstractmethod
    def list_pending(self) -> list[ApprovalRequest]:
        """Return pending approvals in insertion order."""


class InMemoryApprovalStore(ApprovalStore):
    """Local/demo approval store backed by process memory.

    Future PRs can replace this with Postgres, Redis, or another durable store
    without changing approval contracts.
    """

    def __init__(self) -> None:
        """Create an empty in-memory approval store."""

        self._requests: dict[str, ApprovalRequest] = {}

    def create(self, request: ApprovalRequest) -> ApprovalRequest:
        """Create an approval request, preserving insertion order."""

        if request.approval_id in self._requests:
            raise ApprovalStateError(f"Approval '{request.approval_id}' already exists.")
        self._requests[request.approval_id] = request
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        """Return an approval request or raise a clear error."""

        try:
            return self._requests[approval_id]
        except KeyError:
            raise ApprovalNotFoundError(f"Approval '{approval_id}' was not found.") from None

    def approve(
        self,
        approval_id: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Approve a pending request."""

        return self._decide(
            approval_id=approval_id,
            status=ApprovalStatus.APPROVED,
            decided_by=decided_by,
            reason=reason,
        )

    def reject(
        self,
        approval_id: str,
        decided_by: str,
        reason: str | None = None,
    ) -> ApprovalRequest:
        """Reject a pending request."""

        return self._decide(
            approval_id=approval_id,
            status=ApprovalStatus.REJECTED,
            decided_by=decided_by,
            reason=reason,
        )

    def list_pending(self) -> list[ApprovalRequest]:
        """Return pending approvals in insertion order."""

        return [
            request
            for request in self._requests.values()
            if request.status == ApprovalStatus.PENDING
        ]

    def _decide(
        self,
        *,
        approval_id: str,
        status: ApprovalStatus,
        decided_by: str,
        reason: str | None,
    ) -> ApprovalRequest:
        """Apply a terminal decision to a pending approval."""

        request = self.get(approval_id)
        if request.status != ApprovalStatus.PENDING:
            raise ApprovalStateError(
                f"Approval '{approval_id}' is already {request.status.value}."
            )
        decided_by_value = decided_by.strip()
        if not decided_by_value:
            raise ValueError("decided_by must not be blank")
        update: dict[str, Any] = request.model_dump()
        update.update(
            {
                "status": status,
                "decided_at": datetime.now(UTC),
                "decided_by": decided_by_value,
                "decision_reason": reason.strip() if reason else None,
            }
        )
        decided = ApprovalRequest.model_validate(update)
        self._requests[approval_id] = decided
        return decided
