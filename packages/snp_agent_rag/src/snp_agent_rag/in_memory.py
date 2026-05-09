"""Local in-memory retriever for tests and examples only."""

from snp_agent_rag.contracts import RetrievalRequest, RetrievalResult, RetrievedChunk
from snp_agent_rag.retriever import Retriever


class InMemoryRetriever(Retriever):
    """Deterministic substring retriever backed by in-process chunks."""

    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        """Create a retriever from a stable list of chunks."""

        self._chunks = chunks

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Return chunks whose searchable text contains the query."""

        query = request.query.casefold()
        matches: list[tuple[int, RetrievedChunk]] = []

        for index, chunk in enumerate(self._chunks):
            searchable = " ".join(
                value
                for value in [
                    chunk.chunk_id,
                    chunk.source_id,
                    chunk.title,
                    chunk.uri,
                    chunk.text,
                ]
                if value is not None
            ).casefold()
            if query in searchable:
                matches.append((index, chunk))

        ordered = sorted(
            matches,
            key=lambda item: (
                1 if item[1].score is None else 0,
                -(item[1].score or 0.0),
                item[0],
            ),
        )
        chunks = [chunk for _index, chunk in ordered[: request.top_k]]

        return RetrievalResult(
            query=request.query,
            chunks=chunks,
            metadata={"retriever": "in_memory"},
        )
