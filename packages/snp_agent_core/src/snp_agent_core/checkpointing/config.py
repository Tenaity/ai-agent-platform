"""Configuration contracts for LangGraph checkpointing."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CheckpointBackend(StrEnum):
    """Supported checkpoint backends for graph execution state."""

    NONE = "none"
    MEMORY = "memory"


class CheckpointConfig(BaseModel):
    """Checkpointing configuration selected by runtime processes."""

    model_config = ConfigDict(extra="forbid")

    backend: CheckpointBackend = Field(
        default=CheckpointBackend.NONE,
        description="Checkpoint backend used for LangGraph execution state.",
    )
    namespace: str | None = Field(
        default=None,
        description="Optional checkpoint namespace for separating runtime contexts.",
    )

    @field_validator("namespace")
    @classmethod
    def normalize_namespace(cls, value: str | None) -> str | None:
        """Treat blank namespace values as absent configuration."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
