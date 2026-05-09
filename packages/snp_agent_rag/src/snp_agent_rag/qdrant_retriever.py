"""Qdrant retriever adapter implementing the platform Retriever contract.

This module provides ``QdrantRetriever``, a production-shaped adapter that
queries an existing Qdrant collection and converts the results into the
platform's ``RetrievalResult`` / ``RetrievedChunk`` contracts.

Design decisions
----------------
- The Qdrant client is injected at construction time so tests can pass a fake
  without starting a real Qdrant server.
- Payload field keys are configurable via ``QdrantRetrieverConfig`` so the
  adapter remains domain-neutral.
- ``request.top_k`` overrides ``config.top_k_default`` when provided.
- Missing optional payload fields (title, uri, source_id) are handled safely;
  only ``text`` is required.
- Score is read from the Qdrant ``ScoredPoint.score`` field and clamped to the
  ``[0, 1]`` range accepted by ``RetrievedChunk``.  Raw Qdrant cosine scores
  can exceed 1.0 due to floating-point rounding; clamping prevents validation
  errors.
- Simple ``key=value`` filters from ``request.filters`` are translated into a
  Qdrant ``Filter`` with ``must`` ``FieldCondition`` clauses.
  Only scalar string and integer values are supported.  Non-scalar values are
  skipped with a ``warnings.warn``.  Complex filter expressions (range, geo,
  nested) are not supported and must not be passed silently — callers should
  pre-validate filter types before invoking the retriever.
- The adapter does not perform document ingestion, query rewriting, reranking,
  LLM calls, or memory operations.

Non-goals
---------
- No document ingestion.
- No LLM calls.
- No query rewriting or reranking.
- No memory operations.
- No route-handler or app-layer logic.
"""

from __future__ import annotations

import uuid
import warnings
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    HasIdCondition,
    HasVectorCondition,
    IsEmptyCondition,
    IsNullCondition,
    MatchValue,
    NestedCondition,
    ScoredPoint,
)

from snp_agent_rag.contracts import (
    RetrievalRequest,
    RetrievalResult,
    RetrievalSourceType,
    RetrievedChunk,
)
from snp_agent_rag.qdrant_config import QdrantRetrieverConfig
from snp_agent_rag.retriever import Retriever

# Union of all types accepted by Filter.must — required for mypy invariant list check.
_MustCondition = (
    FieldCondition
    | IsEmptyCondition
    | IsNullCondition
    | HasIdCondition
    | HasVectorCondition
    | NestedCondition
    | Filter
)

# Score values from Qdrant can slightly exceed [0, 1] due to floating-point
# rounding in cosine similarity.  Clamp before passing to RetrievedChunk.
_SCORE_MIN = 0.0
_SCORE_MAX = 1.0


class QdrantRetriever(Retriever):
    """Production-shaped Qdrant retriever adapter.

    Implements the platform ``Retriever`` interface by querying an existing
    Qdrant collection via ``qdrant-client``.

    The Qdrant client is injected so the adapter can be unit-tested without
    a running Qdrant server.  In production, pass ``None`` for ``client``
    and the adapter will construct a ``QdrantClient`` from the config URL
    and API key.

    Parameters
    ----------
    config:
        Validated ``QdrantRetrieverConfig`` with connection and payload-mapping
        settings.
    client:
        Optional pre-built ``QdrantClient``.  Pass a fake/mock in tests.
        When ``None``, the adapter creates a client from ``config.url`` and
        ``config.api_key``.

    Example (production)::

        from snp_agent_rag import QdrantRetriever, QdrantRetrieverConfig

        config = QdrantRetrieverConfig(
            url=os.environ["QDRANT_URL"],
            api_key=os.environ.get("QDRANT_API_KEY"),
            collection_name="customer_service_knowledge",
        )
        retriever = QdrantRetriever(config=config)
        result = retriever.retrieve(request)

    Example (tests)::

        retriever = QdrantRetriever(config=config, client=fake_client)
    """

    def __init__(
        self,
        config: QdrantRetrieverConfig,
        client: QdrantClient | None = None,
    ) -> None:
        """Build the adapter.

        When ``client`` is ``None`` the adapter creates a ``QdrantClient``
        connected to ``config.url`` with optional ``config.api_key``.
        """
        self._config = config
        self._client: QdrantClient = client or QdrantClient(
            url=config.url,
            api_key=config.api_key,
            timeout=config.timeout_seconds,
        )

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Query Qdrant and return a validated ``RetrievalResult``.

        The method:

        1. Resolves ``top_k`` from the request, falling back to
           ``config.top_k_default``.
        2. Translates ``request.filters`` into a Qdrant ``Filter`` (scalar
           key/value pairs only).
        3. Calls ``client.query_points`` with the resolved limit and filter.
        4. Converts each ``ScoredPoint`` into a ``RetrievedChunk`` using the
           payload key mapping from ``config``.
        5. Returns a ``RetrievalResult`` with the original query and chunks.

        Missing payload fields
        ----------------------
        - ``text``: when missing, the chunk is skipped and a warning is logged.
          An empty ``text`` field would fail ``RetrievedChunk`` validation.
        - ``source_id``: falls back to the Qdrant point ID as a string.
        - ``title`` and ``uri``: ``None`` when missing.

        Parameters
        ----------
        request:
            Validated ``RetrievalRequest`` from the calling agent node.

        Returns
        -------
        RetrievalResult
            Validated result with chunks in Qdrant score order (descending).
            Returns ``chunks=[]`` when no points match.
        """
        top_k = request.top_k if request.top_k else self._config.top_k_default
        query_filter = _build_filter(request.filters)

        # ``query_points`` is the modern unified search API in qdrant-client >= 1.9.
        # We pass ``query=None`` to perform a scroll/filter-only query when no
        # embedding vector is available.  In future PRs, a pre-computed query
        # vector will be passed here from the agent graph.
        response = self._client.query_points(
            collection_name=self._config.collection_name,
            query=None,
            using=self._config.vector_name,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            timeout=self._config.timeout_seconds,
        )

        chunks: list[RetrievedChunk] = []
        for point in response.points:
            chunk = _point_to_chunk(point, self._config)
            if chunk is not None:
                chunks.append(chunk)

        return RetrievalResult(
            query=request.query,
            chunks=chunks,
            metadata={
                "retriever": "qdrant",
                "collection": self._config.collection_name,
                "top_k_requested": top_k,
                "chunks_returned": len(chunks),
            },
        )


def _build_filter(filters: dict[str, Any]) -> Filter | None:
    """Translate a flat key/value filter dict into a Qdrant ``Filter``.

    Only scalar string and integer values are supported.  Non-scalar values
    produce a ``UserWarning`` and are skipped rather than raising an exception
    or silently producing incorrect results.

    Returns ``None`` when the filter dict is empty or all values are skipped.

    Parameters
    ----------
    filters:
        Flat key/value filter pairs from ``RetrievalRequest.filters``.

    Returns
    -------
    Filter | None
        Qdrant ``Filter`` with ``must`` conditions, or ``None`` for no filter.
    """
    if not filters:
        return None

    must_conditions: list[_MustCondition] = []
    for key, value in filters.items():
        if isinstance(value, (str, int)):
            must_conditions.append(
                FieldCondition(key=key, match=MatchValue(value=value))
            )
        else:
            warnings.warn(
                f"QdrantRetriever: filter key '{key}' has unsupported value type "
                f"{type(value).__name__!r}. Only str and int are supported. "
                "This filter condition has been skipped.",
                UserWarning,
                stacklevel=4,
            )

    if not must_conditions:
        return None

    return Filter(must=must_conditions)


def _point_to_chunk(
    point: ScoredPoint,
    config: QdrantRetrieverConfig,
) -> RetrievedChunk | None:
    """Convert a Qdrant ``ScoredPoint`` to a ``RetrievedChunk``.

    Returns ``None`` when the required ``text`` payload field is missing or
    blank so that callers can skip invalid points rather than raising.

    Parameters
    ----------
    point:
        A ``ScoredPoint`` returned by ``query_points``.
    config:
        Retriever config providing the payload key mapping.

    Returns
    -------
    RetrievedChunk | None
        Validated chunk, or ``None`` if ``text`` is absent or blank.
    """
    payload = point.payload or {}

    text = payload.get(config.text_payload_key)
    if not isinstance(text, str) or not text.strip():
        warnings.warn(
            f"QdrantRetriever: point {point.id!r} is missing or has blank "
            f"payload key '{config.text_payload_key}'. Skipping point.",
            UserWarning,
            stacklevel=3,
        )
        return None

    source_id_raw = payload.get(config.source_id_payload_key)
    source_id: str = str(source_id_raw) if source_id_raw is not None else str(point.id)

    title_raw = payload.get(config.title_payload_key)
    title: str | None = str(title_raw) if isinstance(title_raw, str) and title_raw.strip() else None

    uri_raw = payload.get(config.uri_payload_key)
    uri: str | None = str(uri_raw) if isinstance(uri_raw, str) and uri_raw.strip() else None

    # Clamp score to [0, 1] — Qdrant cosine similarity can marginally exceed 1.0.
    score: float | None = None
    if isinstance(point.score, (int, float)):
        score = max(_SCORE_MIN, min(_SCORE_MAX, float(point.score)))

    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{config.collection_name}:{point.id}"))

    return RetrievedChunk(
        chunk_id=chunk_id,
        source_id=source_id,
        source_type=RetrievalSourceType.DOCUMENT,
        title=title,
        uri=uri,
        text=text.strip(),
        score=score,
        metadata={
            "qdrant_id": str(point.id),
            "collection": config.collection_name,
        },
    )
