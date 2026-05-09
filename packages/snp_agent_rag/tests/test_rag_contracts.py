"""Tests for RAG contracts, local retrieval, and citation enforcement."""

import pytest
from pydantic import ValidationError

from snp_agent_rag import (
    CitationEnforcer,
    CitationPolicy,
    GroundedAnswer,
    InMemoryRetriever,
    RetrievalRequest,
    RetrievalResult,
    RetrievalSourceType,
    RetrievedChunk,
)


def valid_request(query: str = "opening hours", top_k: int = 5) -> RetrievalRequest:
    """Build a valid retrieval request for tests."""

    return RetrievalRequest(
        query=query,
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        top_k=top_k,
        filters={"locale": "en-US"},
        request_id="request_123",
        run_id="run_123",
        thread_id="thread_123",
        metadata={"source": "test"},
    )


def chunk(
    chunk_id: str,
    text: str,
    score: float | None = None,
    title: str | None = None,
) -> RetrievedChunk:
    """Build a retrieved chunk for tests."""

    return RetrievedChunk(
        chunk_id=chunk_id,
        source_id=f"source-{chunk_id}",
        source_type=RetrievalSourceType.DOCUMENT,
        title=title or f"Title {chunk_id}",
        uri=f"https://example.invalid/{chunk_id}",
        text=text,
        score=score,
    )


def test_valid_retrieval_request() -> None:
    """A valid request preserves query, routing fields, filters, and metadata."""

    request = valid_request()

    assert request.query == "opening hours"
    assert request.top_k == 5
    assert request.filters == {"locale": "en-US"}
    assert request.metadata == {"source": "test"}


def test_invalid_blank_query_rejected() -> None:
    """Blank retrieval queries are invalid."""

    with pytest.raises(ValidationError):
        valid_request(query=" ")


def test_top_k_must_be_positive() -> None:
    """Retrieval requests must ask for at least one chunk."""

    with pytest.raises(ValidationError):
        valid_request(top_k=0)


def test_retrieved_chunk_validates_score_range() -> None:
    """Chunk scores must be normalized when present."""

    with pytest.raises(ValidationError):
        chunk("bad-score", "Opening hours are published online.", score=1.1)

    with pytest.raises(ValidationError):
        chunk("negative-score", "Opening hours are published online.", score=-0.1)


def test_in_memory_retriever_returns_matching_chunks() -> None:
    """The local retriever returns chunks that contain the query."""

    retriever = InMemoryRetriever(
        [
            chunk("hours", "Opening hours are 08:00 to 17:00.", score=0.8),
            chunk("tracking", "Container tracking uses the shipment code.", score=0.9),
        ]
    )

    result = retriever.retrieve(valid_request("opening hours"))

    assert [item.chunk_id for item in result.chunks] == ["hours"]
    assert result.metadata == {"retriever": "in_memory"}


def test_in_memory_retriever_respects_top_k() -> None:
    """The local retriever limits deterministic matches to top_k."""

    retriever = InMemoryRetriever(
        [
            chunk("low", "Support ticket guidance.", score=0.2),
            chunk("high", "Support ticket escalation.", score=0.9),
            chunk("medium", "Support ticket routing.", score=0.5),
        ]
    )

    result = retriever.retrieve(valid_request("support ticket", top_k=2))

    assert [item.chunk_id for item in result.chunks] == ["high", "medium"]


def test_in_memory_retriever_returns_empty_result_when_no_match() -> None:
    """The local retriever returns no chunks when the query does not match."""

    retriever = InMemoryRetriever([chunk("hours", "Opening hours are 08:00 to 17:00.")])

    result = retriever.retrieve(valid_request("billing adjustment"))

    assert result.chunks == []


def test_citation_enforcer_creates_citations_from_chunks() -> None:
    """Citation enforcement creates citations only from retrieved chunks."""

    retrieval_result = RetrievalResult(
        query="opening hours",
        chunks=[chunk("hours", "Opening hours are 08:00 to 17:00.", score=0.8)],
    )

    grounded = CitationEnforcer().enforce(
        answer="Opening hours are 08:00 to 17:00.",
        retrieval_result=retrieval_result,
        policy=CitationPolicy(require_citations=True, min_citations=1),
    )

    assert grounded.grounded is True
    assert grounded.missing_citations is False
    assert len(grounded.citations) == 1
    assert grounded.citations[0].source_id == "source-hours"
    assert grounded.citations[0].quote == "Opening hours are 08:00 to 17:00."
    assert grounded.citations[0].metadata["chunk_id"] == "hours"


def test_citation_enforcer_marks_missing_citations_when_no_chunks() -> None:
    """Required citations are marked missing when retrieval returns no chunks."""

    retrieval_result = RetrievalResult(query="opening hours", chunks=[])

    grounded = CitationEnforcer().enforce(
        answer="Opening hours are 08:00 to 17:00.",
        retrieval_result=retrieval_result,
        policy=CitationPolicy(require_citations=True, min_citations=1),
    )

    assert grounded.grounded is False
    assert grounded.missing_citations is True
    assert grounded.citations == []


def test_citation_enforcer_does_not_fabricate_citations() -> None:
    """Citation enforcement never invents sources when retrieval is empty."""

    retrieval_result = RetrievalResult(query="container tracking", chunks=[])

    grounded = CitationEnforcer().enforce(
        answer="Use the tracking page.",
        retrieval_result=retrieval_result,
        policy=CitationPolicy(require_citations=True, min_citations=2),
    )

    assert grounded.citations == []
    assert grounded.metadata["citation_count"] == 0


def test_grounded_answer_serialization() -> None:
    """GroundedAnswer serializes nested core Citation contracts."""

    retrieval_result = RetrievalResult(
        query="support ticket",
        chunks=[chunk("ticket", "Open a support ticket with your shipment reference.")],
    )

    grounded = CitationEnforcer().enforce(
        answer="Open a support ticket with your shipment reference.",
        retrieval_result=retrieval_result,
        policy=CitationPolicy(),
    )

    dumped = grounded.model_dump(mode="json")

    assert dumped["answer"] == "Open a support ticket with your shipment reference."
    assert dumped["grounded"] is True
    assert dumped["missing_citations"] is False
    assert dumped["citations"][0]["source_id"] == "source-ticket"


def test_uncited_answers_can_be_allowed_by_policy() -> None:
    """Policy can explicitly allow answers without retrieval citations."""

    grounded = CitationEnforcer().enforce(
        answer="This answer does not require retrieval.",
        retrieval_result=RetrievalResult(query="small talk", chunks=[]),
        policy=CitationPolicy(require_citations=False),
    )

    assert isinstance(grounded, GroundedAnswer)
    assert grounded.grounded is True
    assert grounded.missing_citations is False
    assert grounded.citations == []
