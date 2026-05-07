"""Runtime-facing contracts shared by apps and platform packages.

These models describe the serialized boundary around agent runtime invocations.
They do not implement execution; adapters such as a future LangGraph runtime
will consume and produce these contracts.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from snp_agent_core.contracts.citations import Citation
from snp_agent_core.contracts.status import AgentRunStatus
from snp_agent_core.contracts.tools import ToolCallRecord


class RuntimeBaseModel(BaseModel):
    """Base contract that keeps runtime payloads explicit and serializable."""

    model_config = ConfigDict(extra="forbid")


class RuntimeHealth(BaseModel):
    """Runtime health state suitable for API responses and probes."""

    status: Literal["ok", "degraded"]


class RuntimeRequest(RuntimeBaseModel):
    """User request accepted by the platform runtime before agent execution.

    The request includes routing and conversation identity but intentionally
    avoids business-specific fields so the core contract stays reusable.
    """

    tenant_id: str = Field(..., description="Tenant or workspace routing identifier.")
    channel: str = Field(..., description="Ingress channel, such as api, web, or worker.")
    user_id: str = Field(..., description="Stable user identifier within the tenant.")
    thread_id: str = Field(..., description="Conversation thread identifier.")
    message: str = Field(..., description="User message to pass into the agent runtime.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable request metadata safe for platform routing and tracing.",
    )

    @field_validator("tenant_id", "channel", "user_id", "thread_id", "message")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank request fields before they enter runtime orchestration."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class RuntimeContext(RuntimeBaseModel):
    """Normalized execution context passed between runtime components.

    Context carries platform-generated request identity and selected agent
    routing data without exposing adapter-specific execution internals.
    """

    request_id: str = Field(..., description="Platform-generated request identifier.")
    tenant_id: str = Field(..., description="Tenant or workspace routing identifier.")
    channel: str = Field(..., description="Ingress channel for this request.")
    user_id: str = Field(..., description="Stable user identifier within the tenant.")
    thread_id: str = Field(..., description="Conversation thread identifier.")
    agent_id: str = Field(..., description="Agent selected to handle this request.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable runtime metadata safe for tracing and policy checks.",
    )

    @field_validator("request_id", "tenant_id", "channel", "user_id", "thread_id", "agent_id")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank context identity fields before execution begins."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class RuntimeResponse(RuntimeBaseModel):
    """Result returned by an agent runtime invocation.

    The response captures answer text, provenance, tool audit records, trace
    linkage, and handoff state without depending on a specific graph engine.
    """

    thread_id: str = Field(..., description="Conversation thread identifier.")
    status: AgentRunStatus = Field(..., description="Final or paused agent run status.")
    answer: str | None = Field(default=None, description="Agent answer when one is available.")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Sources that support the answer.",
    )
    tool_calls: list[ToolCallRecord] = Field(
        default_factory=list,
        description="Audited tool call summaries associated with the run.",
    )
    trace_id: str | None = Field(
        default=None,
        description="Optional tracing identifier from the observability layer.",
    )
    handoff_required: bool = Field(
        default=False,
        description="Whether a human or external workflow must take over.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable response metadata safe for clients and logs.",
    )

    @field_validator("thread_id")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank response identity fields before serialization."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("answer", "trace_id")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        """Normalize optional response strings while preserving absent values."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
