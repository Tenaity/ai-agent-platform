# Citation Enforcement

PR-015 adds citation enforcement for answers grounded in retrieved chunks.
Citation enforcement is deterministic and local: it converts retrieved chunks
into existing core `Citation` objects and reports whether the answer satisfies
the configured policy.

## Policy

`CitationPolicy` controls enforcement:

- `require_citations`: require retrieved citations for grounding.
- `min_citations`: minimum citation count needed to mark an answer grounded.
- `allow_uncited_answer`: explicit override for workflows that may answer
  without citations.

When citations are required and retrieval returns no chunks, the result is:

- `grounded=false`
- `missing_citations=true`
- `citations=[]`

When chunks are available, `CitationEnforcer` creates citations from those
chunks only. It does not fabricate sources.

## Quote Handling

Retrieved chunks can be much larger than a citation excerpt. `CitationEnforcer`
uses a compact quote and truncates long text safely instead of embedding huge
chunks in answer provenance.

## Relationship To RAG

RAG answers must be grounded when policy requires citations. This contract is
separate from retrieval infrastructure: a future Qdrant, pgvector, Neo4j,
GraphRAG, or reranking adapter can return `RetrievalResult`, and citation
enforcement can remain unchanged.
