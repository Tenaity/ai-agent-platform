# PR-019: Qdrant Retriever Adapter

## Summary

This PR adds `QdrantRetriever`, a production-shaped retriever adapter that
implements the platform `Retriever` contract (PR-015) against an existing
Qdrant collection.

The adapter is domain-neutral. It lives in `packages/snp_agent_rag` and
contains no customer-service-specific logic. It is not wired into any agent
graph in this PR — that comes later.

---

## Motivation

PR-015 defined the `Retriever` interface and `InMemoryRetriever` for tests.
The current chatbot demo (PR-018) documents Qdrant as the retrieval backend
but has no adapter to actually query it.

This PR adds that adapter so future PRs can wire retrieval into the agent
graph without modifying the platform contracts.

---

## What This PR Does

### `packages/snp_agent_rag/src/snp_agent_rag/`

| File | Action | Description |
|---|---|---|
| `qdrant_config.py` | New | `QdrantRetrieverConfig` Pydantic model |
| `qdrant_retriever.py` | New | `QdrantRetriever(Retriever)` adapter |
| `__init__.py` | Modified | Export `QdrantRetriever`, `QdrantRetrieverConfig` |

### `packages/snp_agent_rag/tests/`

| File | Action | Description |
|---|---|---|
| `test_qdrant_retriever.py` | New | 53 tests, all using fake/mock client |

### Docs

| File | Action | Description |
|---|---|---|
| `docs/qdrant-retriever.md` | New | Full adapter documentation |
| `docs/rag.md` | Updated | QdrantRetriever section, updated non-goals |
| `docs/architecture/overview.md` | Updated | PR-019 in PR history, updated RAG + non-goals sections |
| `.env.example` | Updated | `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` variables |

### Dependencies

| Package | Version | Added |
|---|---|---|
| `qdrant-client` | `>=1.9.0` (installed: 1.17.1) | Yes |

---

## Design Decisions

### Injectable client for testability

The `QdrantClient` is injected at `__init__` time. In production, pass `None`
and the adapter constructs one from `config.url` and `config.api_key`. In
tests, pass a `MagicMock`. No real Qdrant server required in CI.

### Configurable payload keys

All Qdrant payload field names are configurable via `QdrantRetrieverConfig`:
`text_payload_key`, `title_payload_key`, `uri_payload_key`,
`source_id_payload_key`. Defaults match the schema documented in
`examples/current_chatbot_demo/qdrant/payload_schema.example.json`.

### Score clamping

Qdrant cosine similarity can marginally exceed `1.0` due to floating-point
rounding. The adapter clamps scores to `[0.0, 1.0]` before constructing
`RetrievedChunk`, which enforces `ge=0.0, le=1.0`.

### Deterministic chunk_id

`chunk_id` is a `uuid5` derived from `{collection_name}:{qdrant_point_id}`,
ensuring stability across retrieval calls for the same point.

### Scalar filters only

`request.filters` with `str` or `int` values are translated to
`FieldCondition` clauses. Non-scalar values emit a `UserWarning` and are
skipped. Complex filter expressions are unsupported and documented.

### No query vector in this PR

`query_points` is called with `query=None`, performing a scroll/filter-only
query. Passing an embedding vector will come when the agent graph is wired
with a text encoder in a future PR.

---

## Explicitly Not Added

- No document ingestion or indexing
- No embedding vector computation
- No query rewriting or reranking
- No LLM calls
- No memory operations
- No agent graph wiring
- No route handler changes
- No database persistence
- No production secrets

---

## Tests

All 53 new tests use a `MagicMock` Qdrant client. No real Qdrant server is
required in CI.

Test classes:

| Class | Tests | What it covers |
|---|---|---|
| `TestQdrantRetrieverConfig` | 16 | All config validation rules |
| `TestQdrantRetrieverBasic` | 5 | Return types, empty results, metadata |
| `TestQdrantRetrieverPayloadMapping` | 13 | All payload field mappings |
| `TestQdrantRetrieverScores` | 4 | Score preservation and clamping |
| `TestQdrantRetrieverTopK` | 3 | top_k override behavior |
| `TestQdrantRetrieverMissingText` | 4 | Missing/blank text field handling |
| `TestQdrantRetrieverFilters` | 5 | Filter translation and warnings |
| `TestQdrantRetrieverClientCalls` | 4 | Client call parameter verification |

Run tests:

```bash
make test
```

---

## Acceptance Criteria

- [x] `make lint` passes
- [x] `make typecheck` passes
- [x] `make test` passes (246/246: 193 existing + 53 new)
- [x] `make eval` passes
- [x] No real Qdrant server required in tests
- [x] No secrets committed
- [x] `packages/` remain domain-neutral
- [x] `examples/` not imported by packages

---

## Follow-up PRs

| PR | Scope |
|---|---|
| PR-020 | Production-like Mock API Adapter — implement `ToolExecutor` with audited mock responses |
| PR-021 | n8n/Zalo Facade Endpoint — thin HTTP route for Zalo webhook normalization |
| PR-022 | Wire `QdrantRetriever` into the customer service agent graph |
