"""Tests for QdrantRetrieverConfig and QdrantRetriever.

All tests use a fake/mocked Qdrant client. No real Qdrant server is required.
The fake replaces ``client.query_points`` with a callable that returns
deterministic ``QueryResponse`` objects built from ``ScoredPoint`` fixtures.

Design rules enforced by these tests
--------------------------------------
- ``QdrantRetrieverConfig`` rejects blank url and collection_name.
- ``QdrantRetrieverConfig`` rejects non-positive top_k_default and timeout_seconds.
- ``QdrantRetriever`` maps Qdrant payload fields to ``RetrievedChunk`` contracts.
- Missing optional payload fields (title, uri, source_id) are handled safely.
- Missing required text field causes the point to be skipped with a warning.
- ``request.top_k`` overrides ``config.top_k_default``.
- Scores are clamped to [0, 1].
- Empty Qdrant result returns ``RetrievalResult`` with ``chunks=[]``.
- Scalar filters are translated to Qdrant ``Filter`` conditions.
- Non-scalar filter values are warned and skipped.
- No real Qdrant server is contacted.
"""

from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from pydantic import ValidationError
from qdrant_client.http.models import Filter, QueryResponse, ScoredPoint

from snp_agent_rag import QdrantRetriever, QdrantRetrieverConfig, RetrievalRequest, RetrievalResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**overrides: Any) -> QdrantRetrieverConfig:
    """Return a valid QdrantRetrieverConfig with optional field overrides."""
    defaults: dict[str, Any] = {
        "url": "https://qdrant.example.invalid",
        "collection_name": "test_collection",
    }
    defaults.update(overrides)
    return QdrantRetrieverConfig(**defaults)


def _make_request(
    query: str = "container tracking",
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> RetrievalRequest:
    """Return a valid RetrievalRequest for tests."""
    return RetrievalRequest(
        query=query,
        agent_id="test_agent",
        tenant_id="tenant_demo",
        user_id="user_test",
        channel="api",
        top_k=top_k,
        filters=filters or {},
    )


def _make_scored_point(
    point_id: str | int = "point-001",
    score: float = 0.85,
    payload: dict[str, Any] | None = None,
) -> ScoredPoint:
    """Build a minimal ScoredPoint for use in fake query_points responses."""
    return ScoredPoint(
        id=point_id,
        version=1,
        score=score,
        payload=payload,
    )


def _make_fake_client(points: list[ScoredPoint]) -> MagicMock:
    """Return a MagicMock Qdrant client whose query_points returns ``points``."""
    fake_client = MagicMock()
    fake_client.query_points.return_value = QueryResponse(points=points)
    return fake_client


# ---------------------------------------------------------------------------
# QdrantRetrieverConfig validation
# ---------------------------------------------------------------------------


class TestQdrantRetrieverConfig:
    """QdrantRetrieverConfig must validate all required and constrained fields."""

    def test_valid_config_builds_successfully(self) -> None:
        config = _make_config()
        assert config.url == "https://qdrant.example.invalid"
        assert config.collection_name == "test_collection"
        assert config.api_key is None
        assert config.vector_name is None
        assert config.top_k_default == 5
        assert config.timeout_seconds == 10

    def test_api_key_is_optional(self) -> None:
        config = _make_config(api_key=None)
        assert config.api_key is None

    def test_api_key_can_be_set(self) -> None:
        config = _make_config(api_key="test-key-not-real")
        assert config.api_key == "test-key-not-real"

    def test_vector_name_is_optional(self) -> None:
        config = _make_config(vector_name=None)
        assert config.vector_name is None

    def test_vector_name_can_be_set(self) -> None:
        config = _make_config(vector_name="text_vector")
        assert config.vector_name == "text_vector"

    def test_blank_url_rejected(self) -> None:
        with pytest.raises(ValidationError, match="blank"):
            _make_config(url="  ")

    def test_empty_url_rejected(self) -> None:
        with pytest.raises(ValidationError, match="blank"):
            _make_config(url="")

    def test_blank_collection_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="blank"):
            _make_config(collection_name="  ")

    def test_empty_collection_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="blank"):
            _make_config(collection_name="")

    def test_top_k_default_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_config(top_k_default=0)

    def test_top_k_default_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_config(top_k_default=-1)

    def test_timeout_seconds_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_config(timeout_seconds=0)

    def test_timeout_seconds_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_config(timeout_seconds=-5)

    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_config(nonexistent_field="bad")

    def test_payload_key_defaults(self) -> None:
        config = _make_config()
        assert config.text_payload_key == "text"
        assert config.title_payload_key == "title"
        assert config.uri_payload_key == "uri"
        assert config.source_id_payload_key == "source_id"

    def test_payload_keys_are_configurable(self) -> None:
        config = _make_config(
            text_payload_key="content",
            title_payload_key="name",
            uri_payload_key="url",
            source_id_payload_key="doc_id",
        )
        assert config.text_payload_key == "content"
        assert config.title_payload_key == "name"
        assert config.uri_payload_key == "url"
        assert config.source_id_payload_key == "doc_id"


# ---------------------------------------------------------------------------
# QdrantRetriever — basic functionality
# ---------------------------------------------------------------------------


class TestQdrantRetrieverBasic:
    """QdrantRetriever maps Qdrant points to the platform RetrievalResult."""

    def test_returns_retrieval_result_type(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert isinstance(result, RetrievalResult)

    def test_empty_points_returns_empty_chunks(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.chunks == []

    def test_query_is_preserved_in_result(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request(query="opening hours"))
        assert result.query == "opening hours"

    def test_metadata_includes_retriever_key(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.metadata["retriever"] == "qdrant"

    def test_metadata_includes_collection_name(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.metadata["collection"] == "test_collection"


# ---------------------------------------------------------------------------
# QdrantRetriever — payload mapping
# ---------------------------------------------------------------------------


class TestQdrantRetrieverPayloadMapping:
    """Qdrant payload fields are mapped to RetrievedChunk fields."""

    def _retriever_with_point(
        self, payload: dict[str, Any]
    ) -> tuple[QdrantRetriever, RetrievalRequest]:
        point = _make_scored_point(payload=payload)
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        return retriever, _make_request()

    def test_text_is_mapped_from_payload(self) -> None:
        retriever, request = self._retriever_with_point(
            {"text": "Container tracking information."}
        )
        result = retriever.retrieve(request)
        assert result.chunks[0].text == "Container tracking information."

    def test_title_is_mapped_from_payload(self) -> None:
        retriever, request = self._retriever_with_point(
            {"text": "Some text.", "title": "Doc Title"}
        )
        result = retriever.retrieve(request)
        assert result.chunks[0].title == "Doc Title"

    def test_uri_is_mapped_from_payload(self) -> None:
        retriever, request = self._retriever_with_point(
            {"text": "Some text.", "uri": "kb://docs/test"}
        )
        result = retriever.retrieve(request)
        assert result.chunks[0].uri == "kb://docs/test"

    def test_source_id_is_mapped_from_payload(self) -> None:
        retriever, request = self._retriever_with_point(
            {"text": "Some text.", "source_id": "kb-test-v1"}
        )
        result = retriever.retrieve(request)
        assert result.chunks[0].source_id == "kb-test-v1"

    def test_source_id_falls_back_to_point_id_when_missing(self) -> None:
        point = _make_scored_point(point_id="point-abc", payload={"text": "Some text."})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.chunks[0].source_id == "point-abc"

    def test_title_is_none_when_missing(self) -> None:
        retriever, request = self._retriever_with_point({"text": "Some text."})
        result = retriever.retrieve(request)
        assert result.chunks[0].title is None

    def test_uri_is_none_when_missing(self) -> None:
        retriever, request = self._retriever_with_point({"text": "Some text."})
        result = retriever.retrieve(request)
        assert result.chunks[0].uri is None

    def test_chunk_id_is_deterministic_uuid(self) -> None:
        retriever, request = self._retriever_with_point({"text": "Some text."})
        result = retriever.retrieve(request)
        chunk_id = result.chunks[0].chunk_id
        # Must be parseable as a UUID
        parsed = UUID(chunk_id)
        assert str(parsed) == chunk_id

    def test_chunk_id_is_stable_across_calls(self) -> None:
        point = _make_scored_point(point_id="stable-id", payload={"text": "Text."})
        client1 = _make_fake_client([point])
        client2 = _make_fake_client([point])
        retriever1 = QdrantRetriever(config=_make_config(), client=client1)
        retriever2 = QdrantRetriever(config=_make_config(), client=client2)
        result1 = retriever1.retrieve(_make_request())
        result2 = retriever2.retrieve(_make_request())
        assert result1.chunks[0].chunk_id == result2.chunks[0].chunk_id

    def test_source_type_is_document(self) -> None:
        retriever, request = self._retriever_with_point({"text": "Some text."})
        result = retriever.retrieve(request)
        from snp_agent_rag import RetrievalSourceType
        assert result.chunks[0].source_type == RetrievalSourceType.DOCUMENT

    def test_qdrant_id_is_stored_in_metadata(self) -> None:
        point = _make_scored_point(point_id="meta-id", payload={"text": "Some text."})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.chunks[0].metadata["qdrant_id"] == "meta-id"

    def test_custom_payload_keys_are_used(self) -> None:
        config = _make_config(
            text_payload_key="content",
            title_payload_key="name",
            uri_payload_key="url",
            source_id_payload_key="doc_id",
        )
        payload = {
            "content": "Custom text content.",
            "name": "Custom Name",
            "url": "http://custom.invalid",
            "doc_id": "custom-source-001",
        }
        point = _make_scored_point(payload=payload)
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=config, client=client)
        result = retriever.retrieve(_make_request())
        chunk = result.chunks[0]
        assert chunk.text == "Custom text content."
        assert chunk.title == "Custom Name"
        assert chunk.uri == "http://custom.invalid"
        assert chunk.source_id == "custom-source-001"


# ---------------------------------------------------------------------------
# QdrantRetriever — score handling
# ---------------------------------------------------------------------------


class TestQdrantRetrieverScores:
    """Score values from Qdrant are preserved and clamped to [0, 1]."""

    def test_score_is_preserved(self) -> None:
        point = _make_scored_point(score=0.75, payload={"text": "Some text."})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.chunks[0].score == pytest.approx(0.75)

    def test_score_above_one_is_clamped_to_one(self) -> None:
        point = _make_scored_point(score=1.0001, payload={"text": "Some text."})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.chunks[0].score == pytest.approx(1.0)

    def test_score_below_zero_is_clamped_to_zero(self) -> None:
        point = _make_scored_point(score=-0.001, payload={"text": "Some text."})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.chunks[0].score == pytest.approx(0.0)

    def test_zero_score_is_preserved(self) -> None:
        point = _make_scored_point(score=0.0, payload={"text": "Some text."})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request())
        assert result.chunks[0].score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# QdrantRetriever — top_k handling
# ---------------------------------------------------------------------------


class TestQdrantRetrieverTopK:
    """request.top_k overrides config.top_k_default in the Qdrant query."""

    def test_request_top_k_is_passed_to_qdrant(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(top_k_default=5), client=client)
        retriever.retrieve(_make_request(top_k=3))
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["limit"] == 3

    def test_default_top_k_is_used_when_request_has_default(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(top_k_default=7), client=client)
        # RetrievalRequest defaults top_k=5; pass it explicitly
        retriever.retrieve(_make_request(top_k=5))
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["limit"] == 5

    def test_multiple_chunks_all_returned(self) -> None:
        points = [
            _make_scored_point(
                point_id=f"p-{i}",
                payload={"text": f"Text {i}."},
                score=float(i) / 10,
            )
            for i in range(4)
        ]
        client = _make_fake_client(points)
        retriever = QdrantRetriever(config=_make_config(), client=client)
        result = retriever.retrieve(_make_request(top_k=4))
        assert len(result.chunks) == 4


# ---------------------------------------------------------------------------
# QdrantRetriever — missing text field
# ---------------------------------------------------------------------------


class TestQdrantRetrieverMissingText:
    """Points without a valid text payload are skipped with a warning."""

    def test_point_with_missing_text_is_skipped(self) -> None:
        point = _make_scored_point(payload={"title": "No text here"})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = retriever.retrieve(_make_request())
        assert result.chunks == []
        assert any("missing or has blank" in str(warning.message) for warning in w)

    def test_point_with_blank_text_is_skipped(self) -> None:
        point = _make_scored_point(payload={"text": "   "})
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = retriever.retrieve(_make_request())
        assert result.chunks == []
        assert any("missing or has blank" in str(warning.message) for warning in w)

    def test_point_with_none_payload_is_skipped(self) -> None:
        point = _make_scored_point(payload=None)
        client = _make_fake_client([point])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = retriever.retrieve(_make_request())
        assert result.chunks == []

    def test_valid_points_still_returned_when_one_is_invalid(self) -> None:
        points = [
            _make_scored_point(point_id="bad", payload={}),
            _make_scored_point(point_id="good", payload={"text": "Valid text."}),
        ]
        client = _make_fake_client(points)
        retriever = QdrantRetriever(config=_make_config(), client=client)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = retriever.retrieve(_make_request())
        assert len(result.chunks) == 1
        assert result.chunks[0].text == "Valid text."


# ---------------------------------------------------------------------------
# QdrantRetriever — filter translation
# ---------------------------------------------------------------------------


class TestQdrantRetrieverFilters:
    """Scalar filters are translated; non-scalar values are warned and skipped."""

    def test_no_filter_when_request_filters_empty(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        retriever.retrieve(_make_request(filters={}))
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["query_filter"] is None

    def test_string_filter_is_passed_to_qdrant(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        retriever.retrieve(_make_request(filters={"department": "customer_service"}))
        call_kwargs = client.query_points.call_args.kwargs
        query_filter = call_kwargs["query_filter"]
        assert isinstance(query_filter, Filter)
        assert len(query_filter.must) == 1  # type: ignore[arg-type]

    def test_integer_filter_is_passed_to_qdrant(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        retriever.retrieve(_make_request(filters={"version": 2}))
        call_kwargs = client.query_points.call_args.kwargs
        query_filter = call_kwargs["query_filter"]
        assert isinstance(query_filter, Filter)

    def test_non_scalar_filter_value_warns_and_is_skipped(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            retriever.retrieve(_make_request(filters={"tags": ["a", "b"]}))
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["query_filter"] is None
        assert any("unsupported value type" in str(warning.message) for warning in w)

    def test_mixed_filters_skip_non_scalar_and_pass_scalar(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            retriever.retrieve(_make_request(filters={
                "department": "ops",
                "tags": ["x", "y"],
            }))
        call_kwargs = client.query_points.call_args.kwargs
        query_filter = call_kwargs["query_filter"]
        assert isinstance(query_filter, Filter)
        assert len(query_filter.must) == 1  # type: ignore[arg-type]
        assert any("unsupported value type" in str(warning.message) for warning in w)


# ---------------------------------------------------------------------------
# QdrantRetriever — Qdrant client call params
# ---------------------------------------------------------------------------


class TestQdrantRetrieverClientCalls:
    """The Qdrant client is called with the expected parameters."""

    def test_collection_name_is_passed(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(collection_name="my_col"), client=client)
        retriever.retrieve(_make_request())
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["collection_name"] == "my_col"

    def test_with_payload_is_true(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(), client=client)
        retriever.retrieve(_make_request())
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["with_payload"] is True

    def test_using_vector_name_is_passed(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(vector_name="text_vector"), client=client)
        retriever.retrieve(_make_request())
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["using"] == "text_vector"

    def test_timeout_is_passed(self) -> None:
        client = _make_fake_client([])
        retriever = QdrantRetriever(config=_make_config(timeout_seconds=30), client=client)
        retriever.retrieve(_make_request())
        call_kwargs = client.query_points.call_args.kwargs
        assert call_kwargs["timeout"] == 30
