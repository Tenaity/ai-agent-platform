"""Domain-neutral contracts that describe tool capabilities.

These contracts describe what a tool is allowed to do and what schemas it
accepts or returns. They deliberately do not include execution callables,
provider SDK clients, credentials, or policy enforcement; those concerns belong
behind the future Tool Gateway.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolRiskLevel(StrEnum):
    """Risk tier used by future policy layers to classify tool capabilities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolExecutionMode(StrEnum):
    """Execution mode describing the side-effect profile of a tool."""

    READ = "read"
    WRITE = "write"
    SIDE_EFFECT = "side_effect"


class ToolSpec(BaseModel):
    """Serializable description of a tool capability.

    `ToolSpec` is a registry contract only. It defines names, schemas, scopes,
    risk, and approval requirements so future gateways can enforce policy
    before execution exists.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Stable unique tool name.")
    description: str = Field(..., description="Human-readable capability summary.")
    risk_level: ToolRiskLevel = Field(..., description="Risk tier for policy decisions.")
    execution_mode: ToolExecutionMode = Field(
        ...,
        description="Whether the tool reads, writes, or performs side effects.",
    )
    input_schema: dict[str, Any] = Field(
        ...,
        description="JSON-schema-like contract for tool inputs.",
    )
    output_schema: dict[str, Any] = Field(
        ...,
        description="JSON-schema-like contract for tool outputs.",
    )
    required_scopes: list[str] = Field(
        ...,
        description="Authorization scopes required before the tool may run.",
    )
    approval_required: bool = Field(
        default=False,
        description="Whether a human or policy approval is required before execution.",
    )
    timeout_seconds: int = Field(
        default=30,
        gt=0,
        description="Maximum execution time budget in seconds.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Domain-neutral labels for discovery and filtering.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable registry metadata safe for clients and logs.",
    )

    @field_validator("name", "description")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        """Reject blank identity fields and normalize surrounding whitespace."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("required_scopes", "tags")
    @classmethod
    def reject_blank_string_items(cls, value: list[str]) -> list[str]:
        """Reject blank list items and normalize surrounding whitespace."""

        normalized: list[str] = []
        for item in value:
            stripped = item.strip()
            if not stripped:
                raise ValueError("list items must not be blank")
            normalized.append(stripped)
        return normalized
