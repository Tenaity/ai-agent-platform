"""State schema for the customer service LangGraph sample."""

from typing import Any, NotRequired, TypedDict

from snp_agent_rag import GroundedAnswer, RetrievalResult
from snp_agent_tools import ToolExecutionResult


class CustomerServiceState(TypedDict):
    """Typed graph state for the deterministic customer service demo workflow."""

    thread_id: str
    tenant_id: str
    user_id: str
    channel: str
    message: str
    intent: NotRequired[str | None]
    safety_decision: NotRequired[str | None]
    retrieval_result: NotRequired[RetrievalResult | None]
    grounded_answer: NotRequired[GroundedAnswer | None]
    tool_result: NotRequired[ToolExecutionResult | None]
    final_answer: NotRequired[str | None]
    handoff_required: NotRequired[bool]
    metadata: NotRequired[dict[str, Any]]
