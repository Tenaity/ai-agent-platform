"""Qdrant retriever adapter configuration contract.

This module defines the typed configuration for the Qdrant retriever adapter.
It is intentionally domain-neutral: it carries no SNP-specific field names
except default values that match the customer-service knowledge base schema
documented in ``examples/current_chatbot_demo/qdrant/config.example.yaml``.

Configuration should be loaded from environment variables or a secrets manager.
Do not commit real Qdrant URLs or API keys to source control.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QdrantRetrieverConfig(BaseModel):
    """Validated configuration for the Qdrant retriever adapter.

    All connection and payload-mapping settings are expressed here so that
    the adapter itself contains no hard-coded values. The defaults reflect
    the schema documented in ``qdrant/payload_schema.example.json``.

    Extension points
    ----------------
    - Override ``vector_name`` when using named vectors in the collection.
    - Set ``api_key`` from an environment variable; never pass it as a literal.
    - Lower ``top_k_default`` when retrieving from high-noise collections.

    Invariants
    ----------
    - ``url`` and ``collection_name`` must be non-blank.
    - ``top_k_default`` and ``timeout_seconds`` must be positive integers.
    """

    model_config = ConfigDict(extra="forbid")

    url: str = Field(
        ...,
        description="Qdrant server URL. Load from environment variable QDRANT_URL.",
    )
    api_key: str | None = Field(
        default=None,
        description=(
            "Qdrant API key for cloud clusters. "
            "Load from environment variable QDRANT_API_KEY. "
            "Leave None for unauthenticated local instances."
        ),
    )
    collection_name: str = Field(
        ...,
        description="Qdrant collection to query for retrieval.",
    )
    vector_name: str | None = Field(
        default=None,
        description=(
            "Named vector to use when the collection has multiple named vectors. "
            "Pass None to use the default (unnamed) vector."
        ),
    )
    text_payload_key: str = Field(
        default="text",
        description="Payload field key that holds the chunk text content.",
    )
    title_payload_key: str = Field(
        default="title",
        description="Payload field key that holds the document title.",
    )
    uri_payload_key: str = Field(
        default="uri",
        description="Payload field key that holds the source URI.",
    )
    source_id_payload_key: str = Field(
        default="source_id",
        description="Payload field key that holds the stable source identifier.",
    )
    top_k_default: int = Field(
        default=5,
        gt=0,
        description="Default number of chunks to retrieve when the request does not override.",
    )
    timeout_seconds: int = Field(
        default=10,
        gt=0,
        description="HTTP timeout in seconds for Qdrant requests.",
    )

    @field_validator("url", "collection_name")
    @classmethod
    def reject_blank_required_strings(cls, value: str) -> str:
        """Reject blank connection fields before adapter construction."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped
