"""Domain-neutral contracts for tool execution requests and results."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolExecutionStatus(StrEnum):
    """Terminal status for a tool execution attempt."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"
    TIMED_OUT = "timed_out"


class ToolExecutionRequest(BaseModel):
    """Input envelope for a future tool execution adapter.

    This contract carries caller, agent, and runtime identity plus validated
    tool input. It is domain-neutral and intentionally contains no provider
    clients or execution callables.
    """

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., description="Registered tool name to execute.")
    agent_id: str = Field(..., description="Agent requesting tool execution.")
    tenant_id: str = Field(..., description="Tenant or workspace routing identifier.")
    user_id: str = Field(..., description="Stable user identifier within the tenant.")
    channel: str = Field(..., description="Ingress channel for this execution request.")
    input: dict[str, Any] = Field(..., description="Validated tool input payload.")
    user_scopes: list[str] = Field(
        ...,
        description="Authorization scopes currently available to the user/session.",
    )
    request_id: str | None = Field(default=None, description="Optional HTTP request ID.")
    run_id: str | None = Field(default=None, description="Optional graph execution ID.")
    thread_id: str | None = Field(default=None, description="Optional conversation thread ID.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable execution metadata safe for audit and tracing.",
    )

    @field_validator("tool_name", "agent_id", "tenant_id", "user_id", "channel")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank required identity fields."""

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

    @field_validator("user_scopes")
    @classmethod
    def reject_blank_scopes(cls, value: list[str]) -> list[str]:
        """Reject blank scopes and normalize surrounding whitespace."""

        normalized: list[str] = []
        for item in value:
            stripped = item.strip()
            if not stripped:
                raise ValueError("user_scopes items must not be blank")
            normalized.append(stripped)
        return normalized


class ToolExecutionResult(BaseModel):
    """Result envelope returned by a tool executor."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., description="Tool name associated with this result.")
    status: ToolExecutionStatus = Field(..., description="Execution outcome.")
    output: dict[str, Any] | None = Field(
        default=None,
        description="Serializable tool output when execution succeeds.",
    )
    error: str | None = Field(
        default=None,
        description="Safe error summary when execution fails.",
    )
    latency_ms: int | None = Field(
        default=None,
        ge=0,
        description="Optional executor-reported latency in milliseconds.",
    )
    approval_required: bool = Field(
        default=False,
        description="Whether approval is required before execution can continue.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable result metadata safe for audit and tracing.",
    )

    @field_validator("tool_name")
    @classmethod
    def reject_blank_tool_name(cls, value: str) -> str:
        """Reject blank tool names."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("error")
    @classmethod
    def normalize_error(cls, value: str | None) -> str | None:
        """Normalize optional safe error summaries."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
