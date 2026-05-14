"""Domain-neutral memo memory contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MemoScope(StrEnum):
    """Scope that controls where a memo can be recalled."""

    THREAD = "thread"
    USER = "user"
    TENANT = "tenant"


class MemoRecord(BaseModel):
    """Small explicit memory record for local memo-style recall.

    Memo records are intended for safe, human-readable facts. They are not
    semantic vector memory and should not contain secrets or raw sensitive data.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., description="Stable memo key.")
    value: str = Field(..., description="Memo value.")
    scope: MemoScope = Field(..., description="Recall scope for the memo.")
    tenant_id: str = Field(..., description="Tenant or workspace identifier.")
    user_id: str = Field(..., description="User associated with the memo.")
    thread_id: str | None = Field(default=None, description="Optional thread identifier.")
    created_at: datetime = Field(..., description="UTC-aware creation timestamp.")
    updated_at: datetime = Field(..., description="UTC-aware update timestamp.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable metadata safe for logs and clients.",
    )

    @field_validator("key", "value", "tenant_id", "user_id")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank required strings and trim surrounding whitespace."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("thread_id")
    @classmethod
    def normalize_optional_thread_id(cls, value: str | None) -> str | None:
        """Normalize optional thread id while preserving absent values."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_utc_aware_datetime(cls, value: datetime) -> datetime:
        """Require timezone-aware datetimes and normalize them to UTC."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_thread_id_for_thread_scope(self) -> MemoRecord:
        """Thread-scoped memos must include the thread they belong to."""

        if self.scope == MemoScope.THREAD and self.thread_id is None:
            raise ValueError("thread_id is required for thread-scoped memos")
        return self
