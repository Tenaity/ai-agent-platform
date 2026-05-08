"""Policy contracts for deciding tool access.

The policy layer is domain-neutral and only decides whether a tool may be used.
It does not execute tools, call providers, or enforce safety pipelines.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolAccessDecision(StrEnum):
    """Possible outcomes for a tool access policy check."""

    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"


class ToolAccessRequest(BaseModel):
    """Request context needed to decide whether a tool may be used."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(..., description="Agent requesting tool access.")
    tenant_id: str = Field(..., description="Tenant or workspace routing identifier.")
    user_id: str = Field(..., description="Stable user identifier within the tenant.")
    channel: str = Field(..., description="Ingress channel for the request.")
    tool_name: str = Field(..., description="Requested registered tool name.")
    user_scopes: list[str] = Field(
        ...,
        description="Authorization scopes currently available to the user/session.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable policy metadata safe for audit and debugging.",
    )

    @field_validator("agent_id", "tenant_id", "user_id", "channel", "tool_name")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        """Reject blank identity fields and normalize surrounding whitespace."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

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


class ToolAccessResult(BaseModel):
    """Result of evaluating a tool access request against policy."""

    model_config = ConfigDict(extra="forbid")

    decision: ToolAccessDecision = Field(..., description="Policy decision.")
    reason: str = Field(..., description="Human-readable decision reason.")
    required_scopes: list[str] = Field(
        default_factory=list,
        description="Scopes required by the requested tool.",
    )
    missing_scopes: list[str] = Field(
        default_factory=list,
        description="Required scopes missing from the request.",
    )
    approval_required: bool = Field(
        default=False,
        description="Whether approval is required before future execution.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable result metadata safe for audit and debugging.",
    )

    @field_validator("reason")
    @classmethod
    def reject_blank_reason(cls, value: str) -> str:
        """Require a clear reason for every decision."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("required_scopes", "missing_scopes")
    @classmethod
    def reject_blank_scope_items(cls, value: list[str]) -> list[str]:
        """Reject blank scope items and normalize surrounding whitespace."""

        normalized: list[str] = []
        for item in value:
            stripped = item.strip()
            if not stripped:
                raise ValueError("scope items must not be blank")
            normalized.append(stripped)
        return normalized


class ToolPolicy(BaseModel):
    """Static allow/deny policy for tool access decisions."""

    model_config = ConfigDict(extra="forbid")

    allowed_tools: list[str] = Field(
        default_factory=list,
        description="Tool names that may be considered for access.",
    )
    denied_tools: list[str] = Field(
        default_factory=list,
        description="Tool names that are always denied.",
    )
    approval_required_tools: list[str] = Field(
        default_factory=list,
        description="Tool names that require approval before execution.",
    )
    default_decision: ToolAccessDecision = Field(
        default=ToolAccessDecision.DENIED,
        description="Decision used when a tool is not explicitly allowed.",
    )

    @field_validator("allowed_tools", "denied_tools", "approval_required_tools")
    @classmethod
    def reject_blank_tool_names(cls, value: list[str]) -> list[str]:
        """Reject blank tool names and normalize surrounding whitespace."""

        normalized: list[str] = []
        for item in value:
            stripped = item.strip()
            if not stripped:
                raise ValueError("tool name items must not be blank")
            normalized.append(stripped)
        return normalized
