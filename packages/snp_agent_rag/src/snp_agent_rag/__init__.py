"""Domain-neutral RAG contracts and citation enforcement primitives."""

from snp_agent_rag.citations import CitationEnforcer, CitationPolicy
from snp_agent_rag.contracts import (
    GroundedAnswer,
    RetrievalRequest,
    RetrievalResult,
    RetrievalSourceType,
    RetrievedChunk,
)
from snp_agent_rag.in_memory import InMemoryRetriever
from snp_agent_rag.retriever import Retriever

__all__ = [
    "CitationEnforcer",
    "CitationPolicy",
    "GroundedAnswer",
    "InMemoryRetriever",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalSourceType",
    "RetrievedChunk",
    "Retriever",
]
