"""Retriever interface for future retrieval adapters."""

from abc import ABC, abstractmethod

from snp_agent_rag.contracts import RetrievalRequest, RetrievalResult


class Retriever(ABC):
    """Abstract retrieval boundary implemented by local or external adapters."""

    @abstractmethod
    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Return retrieval context for a validated request."""
