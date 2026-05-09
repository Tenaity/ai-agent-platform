# Agent RAG Template

Use this template for document QA agents that need retrieval contracts and
grounded citations. It uses `Retriever` and `CitationEnforcer` boundaries but
does not include a vector database, document ingestion, or real LLM calls.

## Intended Use

- Contract-first document QA.
- Local tests with fake `RetrievedChunk` fixtures.
- Future adapters such as Qdrant, pgvector, Neo4j, or GraphRAG.

Keep production retrieval adapters outside app route handlers.
