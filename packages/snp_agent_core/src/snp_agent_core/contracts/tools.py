"""Tool call audit contracts for runtime responses."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolCallRecord(BaseModel):
    """Serializable summary of a tool call requested through the Tool Gateway.

    The record captures audit metadata without embedding raw tool inputs,
    outputs, credentials, or provider-specific payloads in core contracts.
    """

    model_config = ConfigDict(extra="forbid")

    tool: str = Field(..., description="Registered tool name.")
    status: str = Field(..., description="Tool execution status reported by the gateway.")
    latency_ms: int | None = Field(
        default=None,
        ge=0,
        description="Optional non-negative tool latency in milliseconds.",
    )
    input_summary: str | None = Field(
        default=None,
        description="Safe, concise description of the tool input.",
    )
    output_summary: str | None = Field(
        default=None,
        description="Safe, concise description of the tool output.",
    )
    error: str | None = Field(
        default=None,
        description="Safe error summary when the tool call failed.",
    )

    @field_validator("tool", "status")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank tool audit fields that are required for traceability."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("input_summary", "output_summary", "error")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        """Normalize optional summaries while keeping absent values as null."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
