"""Citation enforcement for retrieved context."""

from pydantic import Field

from snp_agent_core.contracts import Citation
from snp_agent_rag.contracts import GroundedAnswer, RagBaseModel, RetrievalResult

MAX_QUOTE_CHARS = 240


class CitationPolicy(RagBaseModel):
    """Policy that defines whether answers must cite retrieved chunks."""

    require_citations: bool = Field(
        default=True,
        description="Whether answers must include citations from retrieval context.",
    )
    min_citations: int = Field(
        default=1,
        ge=0,
        description="Minimum citations required for the answer to be grounded.",
    )
    allow_uncited_answer: bool = Field(
        default=False,
        description="Whether an answer may be grounded without citations.",
    )


class CitationEnforcer:
    """Create citations from retrieval results without fabricating sources."""

    def enforce(
        self,
        answer: str,
        retrieval_result: RetrievalResult,
        policy: CitationPolicy,
    ) -> GroundedAnswer:
        """Return a grounded answer according to citation policy."""

        citations = [
            Citation(
                source_id=chunk.source_id,
                title=chunk.title or chunk.source_id,
                uri=chunk.uri,
                quote=_truncate_quote(chunk.text),
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "source_type": chunk.source_type.value,
                    "score": chunk.score,
                },
            )
            for chunk in retrieval_result.chunks
        ]

        if not policy.require_citations or policy.allow_uncited_answer:
            return GroundedAnswer(
                answer=answer,
                citations=citations,
                grounded=True,
                missing_citations=False,
                metadata={"required_citations": policy.require_citations},
            )

        grounded = len(citations) >= policy.min_citations
        return GroundedAnswer(
            answer=answer,
            citations=citations,
            grounded=grounded,
            missing_citations=not grounded,
            metadata={
                "required_citations": policy.require_citations,
                "min_citations": policy.min_citations,
                "citation_count": len(citations),
            },
        )


def _truncate_quote(text: str) -> str:
    """Return a compact quote without exposing full retrieved chunks."""

    stripped = " ".join(text.split())
    if len(stripped) <= MAX_QUOTE_CHARS:
        return stripped
    return f"{stripped[: MAX_QUOTE_CHARS - 3].rstrip()}..."
