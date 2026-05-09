"""Typed state sketch for the current chatbot demo reference agent.

This state schema documents the fields that the future customer-service graph
nodes will read and write. It uses ``TypedDict`` with ``total=False`` so that
nodes can add fields incrementally as the demo evolves.

When promoting this agent to production, consider:
- Freezing the schema and validating fields at graph boundaries.
- Using Pydantic models instead of TypedDict for stricter validation.
- Splitting state into sub-schemas per graph branch if the state grows large.

Field groups
------------
Identity / routing:
    tenant_id, user_id, channel, thread_id, request_id

Input:
    message

Safety:
    safety_decision — output of SafetyPipeline.check_input()

Intent routing:
    intent — one of: "rag", "tool", "direct_answer"

RAG branch:
    retrieval_query    — reformulated query sent to the Retriever
    retrieval_results  — list of RetrievalResult objects from the Retriever
    citations          — citation objects for CitationEnforcer grounding

Tool branch:
    tool_name    — name of the selected ToolSpec
    tool_result  — raw dict returned by the ToolExecutor adapter

Output:
    answer — final formatted response text
"""

from __future__ import annotations

from typing import Any, TypedDict


class CurrentChatbotDemoState(TypedDict, total=False):
    """State fields expected by the future customer-service graph.

    All fields are optional (total=False) to support incremental node-by-node
    population of the state during graph execution.
    """

    # Identity / routing fields
    tenant_id: str
    user_id: str
    channel: str
    thread_id: str
    request_id: str

    # Input
    message: str

    # Safety precheck output
    # Values: "allowed", "rejected_by_safety", "requires_human", "redacted"
    safety_decision: str

    # Intent routing output
    # Values: "rag", "tool", "direct_answer"
    intent: str

    # RAG branch fields
    retrieval_query: str
    retrieval_results: list[Any]  # list[RetrievalResult] when RAG is implemented
    citations: list[Any]          # list[Citation] for CitationEnforcer

    # Tool branch fields
    tool_name: str
    tool_result: dict[str, Any]  # raw ToolExecutor response dict

    # Output
    answer: str
