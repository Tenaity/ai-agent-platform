"""Domain-neutral contracts for safety checks around agent execution.

These models define the serialized boundary for deterministic safety checks.
They intentionally do not describe a moderation provider, LLM judge, product
domain, or storage backend.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SafetyStage(StrEnum):
    """Runtime boundary where a safety check is applied."""

    INPUT = "input"
    TOOL = "tool"
    OUTPUT = "output"


class SafetyDecision(StrEnum):
    """Decision returned by a safety checker or pipeline."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    REDACTED = "redacted"


class SafetySeverity(StrEnum):
    """Severity level for a safety decision."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyBaseModel(BaseModel):
    """Base model for safety contracts with explicit fields only."""

    model_config = ConfigDict(extra="forbid")


class SafetyCheckRequest(SafetyBaseModel):
    """Content and runtime identity needed to evaluate a safety boundary."""

    stage: SafetyStage = Field(..., description="Boundary being checked.")
    agent_id: str = Field(..., description="Agent selected for this safety check.")
    tenant_id: str = Field(..., description="Tenant or workspace routing identifier.")
    user_id: str = Field(..., description="Stable user identifier within the tenant.")
    channel: str = Field(..., description="Ingress or egress channel for this content.")
    content: str = Field(..., description="Text content to evaluate.")
    request_id: str | None = Field(
        default=None,
        description="Optional platform request correlation identifier.",
    )
    run_id: str | None = Field(
        default=None,
        description="Optional platform run identifier when one already exists.",
    )
    thread_id: str | None = Field(
        default=None,
        description="Optional conversation thread identifier.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable metadata for deterministic policy decisions.",
    )

    @field_validator("agent_id", "tenant_id", "user_id", "channel", "content")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank identity and content fields before safety evaluation."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("request_id", "run_id", "thread_id")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        """Normalize optional identifiers while preserving absent values."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class SafetyCheckResult(SafetyBaseModel):
    """Decision and safe explanation produced by a safety check."""

    decision: SafetyDecision = Field(..., description="Safety decision for the content.")
    severity: SafetySeverity = Field(..., description="Severity associated with the decision.")
    reason: str = Field(..., description="Safe explanation that must not leak sensitive content.")
    redacted_content: str | None = Field(
        default=None,
        description="Redacted replacement content when the decision is redacted.",
    )
    flags: list[str] = Field(
        default_factory=list,
        description="Domain-neutral flag identifiers raised by the checker.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable metadata safe for logs and response boundaries.",
    )

    @field_validator("reason")
    @classmethod
    def reject_blank_reason(cls, value: str) -> str:
        """Require every decision to include a non-empty safe reason."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("redacted_content")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        """Normalize optional redacted content while preserving absent values."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
