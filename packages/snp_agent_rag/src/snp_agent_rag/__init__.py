"""Domain-neutral RAG contracts, citation enforcement, and retriever adapters."""

from snp_agent_rag.citations import CitationEnforcer, CitationPolicy
from snp_agent_rag.contracts import (
    GroundedAnswer,
    RetrievalRequest,
    RetrievalResult,
    RetrievalSourceType,
    RetrievedChunk,
)
from snp_agent_rag.in_memory import InMemoryRetriever
from snp_agent_rag.qdrant_config import QdrantRetrieverConfig
from snp_agent_rag.qdrant_retriever import QdrantRetriever
from snp_agent_rag.retriever import Retriever

__all__ = [
    "CitationEnforcer",
    "CitationPolicy",
    "GroundedAnswer",
    "InMemoryRetriever",
    "QdrantRetriever",
    "QdrantRetrieverConfig",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalSourceType",
    "RetrievedChunk",
    "Retriever",
]
