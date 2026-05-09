# RAG Contracts

PR-015 introduces domain-neutral RAG contracts before adding any production
retrieval infrastructure. The package is a typed boundary for future retrievers,
not a vector database integration and not a document ingestion system.

## What Exists

- `RetrievalRequest`: query, runtime identity, top-k, filters, and metadata.
- `RetrievedChunk`: retrieved text plus source identity, source type, optional
  URI, score, and metadata.
- `RetrievalResult`: original query and deterministic chunk list.
- `GroundedAnswer`: answer text with citations and grounding status.
- `Retriever`: abstract retrieval interface.
- `InMemoryRetriever`: local/test-only deterministic substring retriever.

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

## Non-Goals

This PR does not add:

- real vector database integration
- real Neo4j or GraphRAG integration
- real SQL retrieval
- document ingestion
- reranking
- query rewriting
- real LLM calls
- memory manager
- database persistence
- route handler RAG logic
- production TMS, CRM, Billing, or support integrations

Future adapters should implement `Retriever` inside reusable packages or
integration packages. Apps should stay thin and must not own RAG business logic.
