# RAG Contracts

PR-015 introduces domain-neutral RAG contracts before adding any production
retrieval infrastructure. The package is a typed boundary for future retrievers,
not a vector database integration and not a document ingestion system.

PR-019 adds the first real retriever adapter: `QdrantRetriever`.

## What Exists

- `RetrievalRequest`: query, runtime identity, top-k, filters, and metadata.
- `RetrievedChunk`: retrieved text plus source identity, source type, optional
  URI, score, and metadata.
- `RetrievalResult`: original query and deterministic chunk list.
- `GroundedAnswer`: answer text with citations and grounding status.
- `Retriever`: abstract retrieval interface.
- `InMemoryRetriever`: local/test-only deterministic substring retriever.
- `QdrantRetrieverConfig`: Pydantic config for the Qdrant adapter.
- `QdrantRetriever`: production-shaped Qdrant retriever adapter (PR-019).

`InMemoryRetriever` is only for tests, fixtures, and examples. It performs
case-insensitive substring matching over local chunks, respects `top_k`, sorts
scored matches by score, and makes no external calls.

## Source Types

Retrieval source types are intentionally broad:

- `document`
- `database`
- `graph`
- `web`
- `tool`
- `unknown`

They describe provenance without requiring Qdrant, pgvector, Neo4j, SQL, web
search, or tool-result retrieval to exist today.

## QdrantRetriever (PR-019)

`QdrantRetriever` implements the `Retriever` interface against an existing
Qdrant collection. Key design properties:

- **Injectable client**: the Qdrant client is injected at construction for
  testability. Tests use `MagicMock`; no real server is needed.
- **Configurable payload keys**: text, title, uri, and source_id keys are
  all configurable via `QdrantRetrieverConfig`.
- **Score clamping**: Qdrant cosine scores that slightly exceed `[0, 1]` are
  clamped before passing to `RetrievedChunk`.
- **Scalar filters only**: `request.filters` with `str` or `int` values are
  translated to `FieldCondition` clauses; complex types emit `UserWarning`.
- **Graceful missing fields**: points without a `text` payload are skipped
  with a warning; optional fields (`title`, `uri`, `source_id`) fall back
  to `None` or the Qdrant point ID.

See [qdrant-retriever.md](qdrant-retriever.md) for full documentation.

## Non-Goals

PR-015 and PR-019 do not add:

- document ingestion or indexing
- embedding vector computation
- reranking or query rewriting
- real Neo4j or GraphRAG integration
- real SQL retrieval
- memory manager
- database persistence
- route handler RAG logic
- real LLM calls
- production TMS, CRM, Billing, or support integrations

Future adapters should implement `Retriever` inside reusable packages or
integration packages. Apps should stay thin and must not own RAG business logic.

