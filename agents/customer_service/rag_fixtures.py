"""Fake customer-service RAG chunks for local tests and examples.

These fixtures are static examples only. They do not read documents, call a
retrieval service, or represent production knowledge bases.
"""

from snp_agent_rag import RetrievalSourceType, RetrievedChunk

CUSTOMER_SERVICE_RAG_CHUNKS: list[RetrievedChunk] = [
    RetrievedChunk(
        chunk_id="cs-opening-hours-policy-v1",
        source_id="cs-policy-opening-hours",
        source_type=RetrievalSourceType.DOCUMENT,
        title="Customer Support Opening Hours Policy",
        uri="fixture://customer_service/opening-hours",
        text="Customer support is available Monday through Friday from 08:00 to 17:00.",
        score=0.95,
        metadata={"fixture": True},
    ),
    RetrievedChunk(
        chunk_id="cs-container-tracking-v1",
        source_id="cs-instruction-container-tracking",
        source_type=RetrievalSourceType.DOCUMENT,
        title="Container Tracking Instruction",
        uri="fixture://customer_service/container-tracking",
        text="Ask the customer for a shipment or container code before checking tracking status.",
        score=0.9,
        metadata={"fixture": True},
    ),
    RetrievedChunk(
        chunk_id="cs-support-ticket-v1",
        source_id="cs-instruction-support-ticket",
        source_type=RetrievalSourceType.DOCUMENT,
        title="Support Ticket Instruction",
        uri="fixture://customer_service/support-ticket",
        text="Create a support ticket when the customer reports a shipment exception.",
        score=0.85,
        metadata={"fixture": True},
    ),
]
