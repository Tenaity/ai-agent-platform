"""Citation contracts for provenance-aware agent responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Citation(BaseModel):
    """Reference to a source used to support an agent answer.

    Citations keep answer provenance serializable without coupling the core
    runtime contract to a specific retrieval backend or document store.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Stable source identifier from retrieval or context.")
    title: str = Field(..., description="Human-readable source title.")
    uri: str | None = Field(default=None, description="Optional URL or storage URI for the source.")
    quote: str | None = Field(default=None, description="Optional supporting excerpt.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable source metadata that is safe to expose at this boundary.",
    )

    @field_validator("source_id", "title")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank citation identity fields before responses are serialized."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("uri", "quote")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        """Normalize optional citation text while preserving omitted fields as null."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
