# Qdrant Retriever Adapter

PR-019 adds `QdrantRetriever`, a production-shaped Qdrant retriever adapter
that implements the platform `Retriever` contract defined in PR-015.

This document describes its design, configuration, and usage patterns.

---

## What This Is

`QdrantRetriever` is a **retrieval adapter** — not a chatbot component, not a
vector database manager, and not a document ingestion pipeline.

It sits at the boundary between agent graph nodes and an existing Qdrant
collection. Its job is to accept a `RetrievalRequest`, query Qdrant, and
return a validated `RetrievalResult` with `RetrievedChunk` items.

---

## Architecture Boundary

```
Agent Workflow Graph
        │
        ▼
   RetrievalRequest (validated)
        │
        ▼
   QdrantRetriever  ←── QdrantRetrieverConfig
        │
        ▼
   QdrantClient (injected or constructed from config)
        │
        ▼
   Qdrant Collection (existing, pre-populated)
        │
        ▼
   ScoredPoint[]
        │
        ▼ (payload mapping)
   RetrievedChunk[]
        │
        ▼
   RetrievalResult → CitationEnforcer → GroundedAnswer
```

The adapter is domain-neutral. It does not know about customer service,
logistics, Zalo, or any SNP-specific business rules.

---

## Configuration

`QdrantRetrieverConfig` defines all connection and payload-mapping settings:

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | required | Qdrant server URL |
| `api_key` | `str \| None` | `None` | API key for cloud clusters |
| `collection_name` | `str` | required | Collection to query |
| `vector_name` | `str \| None` | `None` | Named vector (pass `None` for default) |
| `text_payload_key` | `str` | `"text"` | Payload field for chunk text |
| `title_payload_key` | `str` | `"title"` | Payload field for source title |
| `uri_payload_key` | `str` | `"uri"` | Payload field for source URI |
| `source_id_payload_key` | `str` | `"source_id"` | Payload field for source ID |
| `top_k_default` | `int` | `5` | Default retrieval limit |
| `timeout_seconds` | `int` | `10` | HTTP request timeout |

### Validation rules

- `url` and `collection_name` must be non-blank.
- `top_k_default` and `timeout_seconds` must be `> 0`.
- `api_key` is optional (for local unauthenticated Qdrant instances).
- Unknown fields are rejected (`extra="forbid"`).

### Environment variables

Load from environment, never commit real values:

```bash
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=               # leave empty for local
QDRANT_COLLECTION=customer_service_knowledge
```

---

## Usage

### Production (real Qdrant server)

```python
import os
from snp_agent_rag import QdrantRetriever, QdrantRetrieverConfig, RetrievalRequest

config = QdrantRetrieverConfig(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ.get("QDRANT_API_KEY"),
    collection_name=os.environ["QDRANT_COLLECTION"],
)
retriever = QdrantRetriever(config=config)

request = RetrievalRequest(
    query="What is the booking cutoff time?",
    agent_id="snp.customer_service.current_chatbot_demo",
    tenant_id="snp",
    user_id="user_001",
    channel="zalo",
    top_k=5,
)
result = retriever.retrieve(request)

for chunk in result.chunks:
    print(chunk.chunk_id, chunk.score, chunk.text[:80])
```

### Tests (injected fake client)

```python
from unittest.mock import MagicMock
from qdrant_client.http.models import QueryResponse, ScoredPoint
from snp_agent_rag import QdrantRetriever, QdrantRetrieverConfig

config = QdrantRetrieverConfig(
    url="https://qdrant.example.invalid",
    collection_name="test",
)

fake_client = MagicMock()
fake_client.query_points.return_value = QueryResponse(points=[
    ScoredPoint(
        id="p1",
        version=1,
        score=0.85,
        payload={"text": "Booking cutoff is 48 hours before departure.", "source_id": "doc-001"},
    )
])

retriever = QdrantRetriever(config=config, client=fake_client)
result = retriever.retrieve(request)
```

---

## Payload Mapping

Each Qdrant `ScoredPoint.payload` is mapped to `RetrievedChunk` fields using
configurable key names:

| `RetrievedChunk` field | Default payload key | Fallback |
|---|---|---|
| `text` | `"text"` | Point is skipped with `UserWarning` |
| `source_id` | `"source_id"` | Qdrant point ID as string |
| `title` | `"title"` | `None` |
| `uri` | `"uri"` | `None` |

`chunk_id` is a deterministic `uuid5` derived from `{collection_name}:{point_id}`.

---

## Score Handling

Qdrant cosine similarity scores can marginally exceed `1.0` due to
floating-point rounding. The adapter clamps all scores to `[0.0, 1.0]`
before passing them to `RetrievedChunk` (which enforces `ge=0.0, le=1.0`).

---

## Filters

Simple scalar filters from `RetrievalRequest.filters` are translated into
Qdrant `FieldCondition` clauses:

```python
request = RetrievalRequest(
    ...,
    filters={"department": "customer_service", "language": "vi"},
)
```

- **Supported**: `str` and `int` values.
- **Unsupported**: `list`, `dict`, `float`, and other complex types.
  Non-scalar values emit a `UserWarning` and are skipped.

Complex filter expressions (range queries, geo filters, nested conditions)
are not supported. Do not pass them silently — validate filters before
calling the retriever.

---

## Non-Goals

This adapter does not:

- Ingest or index documents into Qdrant.
- Compute or manage embedding vectors.
- Call LLMs or rerank results.
- Rewrite queries.
- Manage memory or conversation state.
- Contain any business logic specific to the customer service domain.

---

## Wiring into an Agent Graph

The adapter is injected at graph construction time. Graph nodes call
`retriever.retrieve(request)` and pass the result to `CitationEnforcer`.

```
# Future PR — not yet wired
retriever = QdrantRetriever(config=config)
result = retriever.retrieve(request)
answer = CitationEnforcer().enforce(
    answer=llm_answer,
    retrieval_result=result,
    policy=CitationPolicy(require_citations=True),
)
```

Runtime wiring into the customer service graph is tracked in PR-020 and
PR-021.

---

## References

- [RAG contracts](rag.md)
- [Citation enforcement](citations.md)
- [Current chatbot demo](../examples/current_chatbot_demo/qdrant/config.example.yaml)
- [Architecture overview](architecture/overview.md)
