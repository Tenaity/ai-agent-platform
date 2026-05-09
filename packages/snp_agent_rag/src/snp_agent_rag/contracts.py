"""Domain-neutral retrieval and grounded answer contracts.

These contracts describe the boundary between agent workflows and retrieval
systems without binding the platform to a vector database, graph database,
document ingestion pipeline, or provider-specific retrieval API.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from snp_agent_core.contracts import Citation


class RetrievalSourceType(StrEnum):
    """Source family for a retrieved chunk."""

    DOCUMENT = "document"
    DATABASE = "database"
    GRAPH = "graph"
    WEB = "web"
    TOOL = "tool"
    UNKNOWN = "unknown"


class RagBaseModel(BaseModel):
    """Base RAG contract that rejects unknown fields at boundaries."""

    model_config = ConfigDict(extra="forbid")


class RetrievalRequest(RagBaseModel):
    """Query and runtime identity used to retrieve grounding context."""

    query: str = Field(..., description="Natural-language retrieval query.")
    agent_id: str = Field(..., description="Agent requesting retrieval context.")
    tenant_id: str = Field(..., description="Tenant or workspace routing identifier.")
    user_id: str = Field(..., description="Stable user identifier within the tenant.")
    channel: str = Field(..., description="Ingress channel for the retrieval request.")
    top_k: int = Field(
        default=5,
        gt=0,
        description="Maximum number of chunks to return.",
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-neutral retrieval filters for future adapters.",
    )
    request_id: str | None = Field(
        default=None,
        description="Optional platform request correlation identifier.",
    )
    run_id: str | None = Field(
        default=None,
        description="Optional platform run identifier.",
    )
    thread_id: str | None = Field(
        default=None,
        description="Optional conversation thread identifier.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable metadata safe for retrieval adapters.",
    )

    @field_validator("query", "agent_id", "tenant_id", "user_id", "channel")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank retrieval fields before adapter execution."""

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


class RetrievedChunk(RagBaseModel):
    """A text chunk returned by retrieval with provenance metadata."""

    chunk_id: str = Field(..., description="Stable identifier for this retrieved chunk.")
    source_id: str = Field(..., description="Stable identifier for the source object.")
    source_type: RetrievalSourceType = Field(..., description="Source family for the chunk.")
    title: str | None = Field(default=None, description="Optional source title.")
    uri: str | None = Field(default=None, description="Optional source URI.")
    text: str = Field(..., description="Retrieved text used for answer grounding.")
    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional normalized relevance score between 0 and 1.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable chunk metadata safe for downstream use.",
    )

    @field_validator("chunk_id", "source_id", "text")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank chunk identity and text fields."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("title", "uri")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        """Normalize optional chunk strings while preserving absent values."""

        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class RetrievalResult(RagBaseModel):
    """Retrieved context returned for a query."""

    query: str = Field(..., description="Original retrieval query.")
    chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Retrieved chunks in deterministic result order.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable retrieval metadata.",
    )

    @field_validator("query")
    @classmethod
    def reject_blank_query(cls, value: str) -> str:
        """Reject blank result queries for traceability."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class GroundedAnswer(RagBaseModel):
    """Answer text with citation grounding status."""

    answer: str = Field(..., description="Answer text produced by a workflow.")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Citations derived from retrieved chunks.",
    )
    grounded: bool = Field(..., description="Whether the answer satisfies citation policy.")
    missing_citations: bool = Field(
        default=False,
        description="Whether required citations were unavailable or insufficient.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable metadata about citation enforcement.",
    )

    @field_validator("answer")
    @classmethod
    def reject_blank_answer(cls, value: str) -> str:
        """Reject blank answer text before citation enforcement output."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped
