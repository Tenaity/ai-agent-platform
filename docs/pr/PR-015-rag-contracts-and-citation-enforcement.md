# PR-015: RAG Contracts + Citation Enforcement

## Summary

Introduce domain-neutral RAG contracts and citation enforcement before adding
real vector databases, document ingestion, GraphRAG, memory, or production
retrieval integrations.

This PR adds typed retrieval contracts, a retriever interface, a local-only
in-memory retriever for tests and fixtures, and a `CitationEnforcer` that
creates core `Citation` objects from retrieved chunks without fabricating
sources.

## Scope

- Add `packages/snp_agent_rag` contracts:
  - `RetrievalSourceType`
  - `RetrievalRequest`
  - `RetrievedChunk`
  - `RetrievalResult`
  - `GroundedAnswer`
- Add `Retriever` interface.
- Add `InMemoryRetriever` for local tests and examples only.
- Add `CitationPolicy` and `CitationEnforcer`.
- Add fake customer-service RAG chunks in `agents/customer_service`.
- Add focused tests for validation, local retrieval, citation creation,
  missing citations, non-fabrication, and serialization.
- Add RAG and citation docs and update repository architecture docs.

## Non-Goals

- No real vector DB integration.
- No real Neo4j integration.
- No real SQL retrieval.
- No document ingestion pipeline.
- No real LLM calls.
- No memory manager.
- No real TMS, CRM, Billing, or support integrations.
- No database persistence.
- No route handler RAG logic.

## Design Notes

The RAG package remains domain-neutral and imports no apps. It reuses the core
`Citation` contract so runtime responses and grounded answers share provenance
shape.

`InMemoryRetriever` is deterministic and local-only. It exists to test the
contract and support fixtures before real retrieval adapters exist.

`CitationEnforcer` prevents citation fabrication by creating citations only
from `RetrievedChunk` objects present in a `RetrievalResult`. If policy requires
citations and retrieval returns no chunks, the answer is marked ungrounded with
missing citations.

Future PRs can add Qdrant, pgvector, Neo4j, reranking, query rewriting,
document ingestion, and GraphRAG behind the `Retriever` interface.

## Acceptance Criteria

- `make lint` passes.
- `make typecheck` passes.
- `make test` passes.
- `make eval` passes.
