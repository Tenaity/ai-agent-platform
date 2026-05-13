"""Domain-neutral human approval contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApprovalStatus(StrEnum):
    """Lifecycle state for a human approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRiskLevel(StrEnum):
    """Risk tier associated with a paused action."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest(BaseModel):
    """Serializable request for human approval before an action proceeds.

    The contract intentionally stores summaries and metadata only. Full raw
    sensitive payloads and secrets should remain outside approval records.
    """

    model_config = ConfigDict(extra="forbid")

    approval_id: str = Field(..., description="Stable approval identifier.")
    agent_id: str = Field(..., description="Agent requesting approval.")
    tenant_id: str = Field(..., description="Tenant or workspace identifier.")
    user_id: str = Field(..., description="User associated with the request.")
    channel: str = Field(..., description="Ingress channel for the approval request.")
    thread_id: str | None = Field(default=None, description="Optional conversation thread id.")
    request_id: str | None = Field(default=None, description="Optional runtime request id.")
    run_id: str | None = Field(default=None, description="Optional runtime run id.")
    action_name: str = Field(..., description="Stable action name requiring approval.")
    action_summary: str = Field(..., description="Safe summary of the proposed action.")
    risk_level: ApprovalRiskLevel = Field(..., description="Risk tier for the action.")
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING,
        description="Current approval state.",
    )
    created_at: datetime = Field(..., description="UTC-aware creation timestamp.")
    decided_at: datetime | None = Field(default=None, description="UTC-aware decision timestamp.")
    decided_by: str | None = Field(default=None, description="User/operator who decided.")
    decision_reason: str | None = Field(default=None, description="Optional safe decision reason.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable metadata safe for logs and clients.",
    )

    @field_validator(
        "approval_id",
        "agent_id",
        "tenant_id",
        "user_id",
        "channel",
        "action_name",
        "action_summary",
    )
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank required strings and trim surrounding whitespace."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("thread_id", "request_id", "run_id", "decided_by", "decision_reason")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        """Normalize optional strings while preserving absent values."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("created_at", "decided_at")
    @classmethod
    def require_utc_aware_datetime(cls, value: datetime | None) -> datetime | None:
        """Require timezone-aware datetimes and normalize them to UTC."""

        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value.astimezone(UTC)
