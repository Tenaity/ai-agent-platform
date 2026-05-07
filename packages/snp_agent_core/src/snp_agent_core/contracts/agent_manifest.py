"""Typed manifest contract for versioned agent definitions.

Agent manifests are the boundary between domain-specific agent folders and the
domain-neutral platform runtime. Keeping this contract explicit prevents prompt
or YAML shape changes from becoming hidden production behavior.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ManifestBaseModel(BaseModel):
    """Base model that rejects unknown manifest keys at contract boundaries."""

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def reject_blank_required_strings(cls, value: object) -> object:
        """Reject blank strings throughout manifest sections before validation."""

        if isinstance(value, str) and not value.strip():
            raise ValueError("field must not be blank")
        return value


class RuntimeManifest(ManifestBaseModel):
    """Runtime graph configuration declared by an agent."""

    type: str = Field(..., description="Runtime implementation family, such as langgraph.")
    graph: str = Field(..., description="Import path for the graph builder function.")
    state_schema: str = Field(..., description="Import path for the graph state schema.")


class ModelPolicyManifest(ManifestBaseModel):
    """Model selection and usage constraints for an agent."""

    provider: str = Field(..., description="Model provider identifier.")
    model: str = Field(..., description="Model identifier approved for this agent.")
    allow_real_calls: bool = Field(
        default=False,
        description="Whether this manifest permits live model calls in the current environment.",
    )


class MemoryManifest(ManifestBaseModel):
    """Memory configuration declared by an agent.

    The core contract names the memory profile without binding the runtime to a
    storage backend or memory implementation.
    """

    profile: str = Field(..., description="Named memory profile for the agent.")
    enabled: bool = Field(default=False, description="Whether memory is enabled for this agent.")


class RetrievalManifest(ManifestBaseModel):
    """Retrieval configuration declared by an agent.

    Retrieval remains optional until RAG contracts and stores are introduced in
    later PRs.
    """

    profile: str = Field(..., description="Named retrieval profile for the agent.")
    enabled: bool = Field(default=False, description="Whether retrieval is enabled for this agent.")


class ToolPolicyManifest(ManifestBaseModel):
    """Tool governance configuration for an agent."""

    allowed: list[str] = Field(
        default_factory=list,
        description="Tool names this agent may request through the Tool Gateway.",
    )
    requires_gateway: bool = Field(
        default=True,
        description="Whether tool execution must flow through the platform Tool Gateway.",
    )


class SafetyManifest(ManifestBaseModel):
    """Safety controls that must be applied around the agent workflow."""

    policy: str = Field(..., description="Named safety policy profile.")
    human_review_required: bool = Field(
        default=False,
        description="Whether outputs require human review before external use.",
    )


class ObservabilityManifest(ManifestBaseModel):
    """Tracing and telemetry expectations for an agent workflow."""

    tracing: bool = Field(default=True, description="Whether workflow tracing is expected.")
    project: str = Field(..., description="Observability project or namespace.")


class EvalManifest(ManifestBaseModel):
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
    runtime: RuntimeManifest
    model_policy: ModelPolicyManifest
    memory: MemoryManifest | None = Field(
        default=None,
        description="Optional memory profile for this agent.",
    )
    retrieval: RetrievalManifest | None = Field(
        default=None,
        description="Optional retrieval profile for this agent.",
    )
    tools: ToolPolicyManifest
    safety: SafetyManifest
    observability: ObservabilityManifest
    eval: EvalManifest
