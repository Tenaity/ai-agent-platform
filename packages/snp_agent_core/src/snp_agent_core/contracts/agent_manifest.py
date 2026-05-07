"""Typed manifest contract for versioned agent definitions.

Agent manifests are the boundary between domain-specific agent folders and the
domain-neutral platform runtime. Keeping this contract explicit prevents prompt
or YAML shape changes from becoming hidden production behavior.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ManifestBaseModel(BaseModel):
    """Base model that rejects unknown manifest keys at contract boundaries."""

    model_config = ConfigDict(extra="forbid")


class RuntimeConfig(ManifestBaseModel):
    """Runtime graph configuration declared by an agent."""

    kind: str = Field(..., description="Runtime implementation family, such as langgraph.")
    entrypoint: str = Field(..., description="Import path or symbolic graph entrypoint.")


class ModelPolicy(ManifestBaseModel):
    """Model selection and usage constraints for an agent."""

    provider: str = Field(..., description="Model provider identifier.")
    model: str = Field(..., description="Model identifier approved for this agent.")
    allow_real_calls: bool = Field(
        default=False,
        description="Whether this manifest permits live model calls in the current environment.",
    )


class ToolPolicy(ManifestBaseModel):
    """Tool governance configuration for an agent."""

    allowed: list[str] = Field(
        default_factory=list,
        description="Tool names this agent may request through the Tool Gateway.",
    )
    requires_gateway: bool = Field(
        default=True,
        description="Whether tool execution must flow through the platform Tool Gateway.",
    )


class SafetyPolicy(ManifestBaseModel):
    """Safety controls that must be applied around the agent workflow."""

    policy: str = Field(..., description="Named safety policy profile.")
    human_review_required: bool = Field(
        default=False,
        description="Whether outputs require human review before external use.",
    )


class ObservabilityPolicy(ManifestBaseModel):
    """Tracing and telemetry expectations for an agent workflow."""

    tracing: bool = Field(default=True, description="Whether workflow tracing is expected.")
    project: str = Field(..., description="Observability project or namespace.")


class EvalPolicy(ManifestBaseModel):
    """Regression evaluation configuration for an agent."""

    dataset: str = Field(..., description="Dataset identifier used for regression evaluation.")
    min_pass_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Minimum acceptable regression pass rate.",
    )


class AgentManifest(ManifestBaseModel):
    """Versioned, typed manifest for a domain-specific agent."""

    id: str = Field(..., description="Stable agent identifier.")
    version: str = Field(..., description="Agent behavior version.")
    owner: str = Field(..., description="Owning team or accountable maintainer.")
    domain: str = Field(..., description="Business or product domain for this agent.")
    runtime: RuntimeConfig
    model_policy: ModelPolicy
    tools: ToolPolicy
    safety: SafetyPolicy
    observability: ObservabilityPolicy
    eval: EvalPolicy

    @field_validator("id", "version", "owner", "domain")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        """Reject blank top-level identity fields before manifests enter the runtime."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("runtime", "model_policy", "tools", "safety", "observability", "eval")
    @classmethod
    def require_sections(cls, value: Any) -> Any:
        """Require each major manifest section to be present and validated."""

        if value is None:
            raise ValueError("manifest section is required")
        return value
