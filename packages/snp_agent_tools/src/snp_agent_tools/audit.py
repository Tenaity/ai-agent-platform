"""Domain-neutral audit contracts for tool call security and operations records.

Audit records produced here are security, operations, and compliance records.
They are NOT LangSmith traces. LangSmith traces are owned by the observability
layer and capture model reasoning, token usage, and latency at the LLM call
boundary. Audit records capture who called which tool, what the policy decided,
and whether execution succeeded — information needed for access review, incident
response, and compliance reporting.

Key design decisions:
- Raw input and output are never stored by default; only key-name summaries are
  kept to prevent PII and sensitive business data from leaking into audit logs.
- ``created_at`` must be timezone-aware UTC so audit timestamps are unambiguous
  across deployments.
- The model uses ``extra="forbid"`` so callers cannot silently smuggle unknown
  fields into the audit record.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolCallAuditStatus(StrEnum):
    """Lifecycle status values for a tool call audit record.

    The status captures the most significant outcome at the point the record
    is written. A single tool execution may produce multiple intermediate
    statuses (e.g., ``allowed`` during policy check, then ``succeeded`` after
    execution), but each ``ToolCallAuditRecord`` captures one status value.
    """

    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class ToolCallAuditRecord(BaseModel):
    """Immutable audit record for a single tool call event.

    Each record captures the identity context, policy outcome, and execution
    result for one tool call attempt. Records are written by the
    ``AuditAwareToolExecutor`` wrapper and collected by a ``ToolCallAuditSink``.

    Design constraints:
    - ``audit_id`` is a caller-supplied string (UUID recommended) to support
      idempotent writes against future persistent sinks.
    - ``input_summary`` and ``output_summary`` should contain key names only,
      never raw values, to avoid capturing PII or sensitive business data.
    - ``error_summary`` must not include stack traces, exception types, or
      implementation details that could aid attackers.
    - ``created_at`` must be timezone-aware UTC to ensure timestamp monotonicity
      across distributed platform deployments.
    - ``metadata`` carries serializable audit-safe context; callers are
      responsible for ensuring values do not include secrets or raw payloads.
    """

    model_config = ConfigDict(extra="forbid")

    audit_id: str = Field(..., description="Unique audit record identifier (UUID recommended).")
    tool_name: str = Field(..., description="Registered name of the tool that was called.")
    agent_id: str = Field(..., description="Agent that initiated the tool call.")
    tenant_id: str = Field(..., description="Tenant or workspace routing identifier.")
    user_id: str = Field(..., description="Stable user identifier within the tenant.")
    channel: str = Field(..., description="Ingress channel for this tool call request.")
    status: ToolCallAuditStatus = Field(
        ...,
        description="Audit status capturing the most significant outcome of this call.",
    )

    # Optional correlation identifiers — populated when the executor context
    # provides them so records can be joined with HTTP traces and graph runs.
    request_id: str | None = Field(
        default=None,
        description="HTTP request correlation identifier, when available.",
    )
    run_id: str | None = Field(
        default=None,
        description="Graph execution run identifier, when available.",
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread identifier, when available.",
    )

    latency_ms: int | None = Field(
        default=None,
        ge=0,
        description="Executor-reported latency in milliseconds, when available.",
    )

    # Summaries intentionally omit raw values to prevent PII leakage.
    input_summary: str | None = Field(
        default=None,
        description=(
            "Summary of tool input fields (key names only, no raw values). "
            "Must not contain PII or sensitive business data."
        ),
    )
    output_summary: str | None = Field(
        default=None,
        description=(
            "Summary of tool output fields (key names only, no raw values). "
            "Must not contain PII or sensitive business data."
        ),
    )
    error_summary: str | None = Field(
        default=None,
        description=(
            "Human-readable error summary on failure. "
            "Must not include stack traces, exception class names, or implementation details."
        ),
    )

    created_at: datetime = Field(
        ...,
        description="UTC timestamp when this audit record was created. Must be timezone-aware.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable audit-safe context. Must not contain secrets or raw payloads.",
    )

    @field_validator("audit_id", "tool_name", "agent_id", "tenant_id", "user_id", "channel")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank required identity and routing fields."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("created_at")
    @classmethod
    def require_utc_aware(cls, value: datetime) -> datetime:
        """Reject naive datetimes to enforce unambiguous UTC audit timestamps.

        A naive ``datetime`` (without ``tzinfo``) cannot be reliably compared
        across time zones and must be rejected at the model boundary.
        """

        if value.tzinfo is None:
            raise ValueError(
                "created_at must be a timezone-aware UTC datetime; "
                "use datetime.now(timezone.utc) or datetime(..., tzinfo=timezone.utc)"
            )
        return value.astimezone(UTC)
