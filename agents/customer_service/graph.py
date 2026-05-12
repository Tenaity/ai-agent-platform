"""Deterministic LangGraph graph for the customer service demo agent."""

from __future__ import annotations

import re
from typing import Any, cast

from langgraph.graph import END, StateGraph

from agents.customer_service.intent import CustomerServiceIntent, classify_intent
from agents.customer_service.mock_api.tool_executor import CustomerServiceMockApiToolExecutor
from agents.customer_service.rag_fixtures import CUSTOMER_SERVICE_RAG_CHUNKS
from agents.customer_service.state import CustomerServiceState
from agents.customer_service.tools import (
    CUSTOMER_SERVICE_TOOL_SPECS,
    create_support_ticket,
)
from snp_agent_rag import (
    CitationEnforcer,
    CitationPolicy,
    GroundedAnswer,
    InMemoryRetriever,
    RetrievalRequest,
    Retriever,
)
from snp_agent_safety import (
    RuleBasedSafetyChecker,
    SafetyCheckRequest,
    SafetyDecision,
    SafetyPipeline,
    SafetyPolicy,
    SafetyStage,
)
from snp_agent_tools import (
    AuditAwareToolExecutor,
    InMemoryToolCallAuditSink,
    PolicyAwareToolExecutor,
    ToolAccessDecision,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolExecutor,
    ToolGateway,
    ToolPolicy,
    ToolRegistry,
)

HELLO_ANSWER = (
    "Hello from snp.customer_service.zalo. Real reasoning, RAG, tools, memory, "
    "and safety will be added in later PRs."
)

_AGENT_ID = "customer_service"
_TRACKING_TOOL = "tracking_container"
_BOOKING_TOOL = "check_booking_status"
_SUPPORT_TOOL = "create_support_ticket"
_CONTAINER_PATTERN = re.compile(r"\b(?:[A-Z]{4}\d{7}|CONT-\d+)\b", re.IGNORECASE)
_BOOKING_PATTERN = re.compile(r"\b(?:BK-\d{4}-\d{4}|BK-\d{3,})\b", re.IGNORECASE)


def _default_safety_pipeline() -> SafetyPipeline:
    """Return the permissive default graph safety pipeline."""

    return SafetyPipeline([RuleBasedSafetyChecker(SafetyPolicy())])


def _default_retriever() -> Retriever:
    """Return local fixture-backed retrieval for graph tests and demos."""

    return InMemoryRetriever(CUSTOMER_SERVICE_RAG_CHUNKS)


def _default_tool_executor() -> ToolExecutor:
    """Build the governed, audited mock API tool executor for the demo graph."""

    registry = ToolRegistry()
    for spec in CUSTOMER_SERVICE_TOOL_SPECS:
        # The reference ToolSpec marks support ticket creation as requiring
        # approval. PR-021 demo graph keeps execution deterministic by allowing
        # the local mock adapter while still flowing through ToolGateway.
        if spec.name == create_support_ticket.name:
            registry.register(spec.model_copy(update={"approval_required": False}))
        else:
            registry.register(spec)

    gateway = ToolGateway(
        registry=registry,
        policy=ToolPolicy(
            allowed_tools=[spec.name for spec in CUSTOMER_SERVICE_TOOL_SPECS],
            default_decision=ToolAccessDecision.DENIED,
        ),
    )
    policy_executor = PolicyAwareToolExecutor(
        gateway=gateway,
        executor=CustomerServiceMockApiToolExecutor(),
    )
    return AuditAwareToolExecutor(
        executor=policy_executor,
        audit_sink=InMemoryToolCallAuditSink(),
    )


def _metadata(state: CustomerServiceState) -> dict[str, Any]:
    """Return mutable graph metadata without mutating the input state."""

    return dict(state.get("metadata") or {})


def _safety_precheck_node(
    safety_pipeline: SafetyPipeline,
) -> Any:
    """Build the safety precheck node."""

    def safety_precheck(state: CustomerServiceState) -> dict[str, Any]:
        result = safety_pipeline.check(
            SafetyCheckRequest(
                stage=SafetyStage.INPUT,
                agent_id=_AGENT_ID,
                tenant_id=state["tenant_id"],
                user_id=state["user_id"],
                channel=state["channel"],
                content=state["message"],
                thread_id=state["thread_id"],
            )
        )
        metadata = _metadata(state)
        metadata["safety_reason"] = result.reason
        metadata["safety_flags"] = result.flags

        if result.decision == SafetyDecision.BLOCKED:
            return {
                "safety_decision": result.decision.value,
                "intent": None,
                "handoff_required": False,
                "final_answer": (
                    "I cannot handle this request because it was blocked by safety policy."
                ),
                "metadata": metadata,
            }

        if result.decision == SafetyDecision.NEEDS_HUMAN_REVIEW:
            return {
                "safety_decision": result.decision.value,
                "intent": None,
                "handoff_required": True,
                "final_answer": (
                    "This request needs human review before I can continue. "
                    "A support teammate should take over."
                ),
                "metadata": metadata,
            }

        if result.decision == SafetyDecision.REDACTED and result.redacted_content is not None:
            metadata["redacted"] = True
            return {
                "safety_decision": result.decision.value,
                "message": result.redacted_content,
                "metadata": metadata,
            }

        return {
            "safety_decision": result.decision.value,
            "handoff_required": False,
            "metadata": metadata,
        }

    return safety_precheck


def classify_intent_node(state: CustomerServiceState) -> dict[str, str]:
    """Classify the current message unless a prior node already completed."""

    if state.get("final_answer"):
        return {}
    return {"intent": classify_intent(state["message"]).value}


def route_intent(state: CustomerServiceState) -> str:
    """Return the next graph branch for the classified intent."""

    if state.get("final_answer"):
        return "format_final_answer"

    intent = state.get("intent") or CustomerServiceIntent.FALLBACK.value
    if intent == CustomerServiceIntent.POLICY_QUESTION.value:
        return "rag_answer"
    if intent == CustomerServiceIntent.CONTAINER_TRACKING.value:
        return "container_tracking"
    if intent == CustomerServiceIntent.BOOKING_STATUS.value:
        return "booking_status"
    if intent == CustomerServiceIntent.SUPPORT_TICKET.value:
        return "support_ticket"
    return "fallback"


def _policy_retrieval_query(message: str) -> str:
    """Map user policy wording to deterministic fixture search queries."""

    lowered = message.casefold()
    if "giờ làm việc" in lowered:
        return "opening hours"
    if "ticket" in lowered or "hỗ trợ" in lowered or "khiếu nại" in lowered:
        return "support ticket"
    if "container" in lowered or "cont" in lowered or "tracking" in lowered:
        return "container tracking"
    return "customer support"


def _rag_answer_node(retriever: Retriever) -> Any:
    """Build the RAG answer node backed by a local/test retriever."""

    def rag_answer(state: CustomerServiceState) -> dict[str, Any]:
        query = _policy_retrieval_query(state["message"])
        retrieval_result = retriever.retrieve(
            RetrievalRequest(
                query=query,
                agent_id=_AGENT_ID,
                tenant_id=state["tenant_id"],
                user_id=state["user_id"],
                channel=state["channel"],
                thread_id=state["thread_id"],
                top_k=3,
            )
        )

        if retrieval_result.chunks:
            source_text = retrieval_result.chunks[0].text
            answer = f"{source_text}"
        else:
            answer = "I could not find a grounded policy answer in the local knowledge fixtures."

        grounded_answer = CitationEnforcer().enforce(
            answer=answer,
            retrieval_result=retrieval_result,
            policy=CitationPolicy(require_citations=True, min_citations=1),
        )
        return {
            "retrieval_result": retrieval_result,
            "grounded_answer": grounded_answer,
            "final_answer": _format_grounded_answer(grounded_answer),
        }

    return rag_answer


def _format_grounded_answer(grounded_answer: GroundedAnswer) -> str:
    """Return deterministic answer text with compact citation metadata."""

    citations = grounded_answer.citations
    if not citations:
        return grounded_answer.answer
    citation_labels = ", ".join(citation.title for citation in citations)
    return f"{grounded_answer.answer}\n\nCitations: {citation_labels}"


def _tool_request(
    *,
    state: CustomerServiceState,
    tool_name: str,
    input_payload: dict[str, Any],
) -> ToolExecutionRequest:
    """Create a governed tool execution request for the demo graph."""

    return ToolExecutionRequest(
        tool_name=tool_name,
        agent_id=_AGENT_ID,
        tenant_id=state["tenant_id"],
        user_id=state["user_id"],
        channel=state["channel"],
        input=input_payload,
        user_scopes=["shipment:read", "booking:read", "support_ticket:write"],
        thread_id=state["thread_id"],
    )


def _extract_container_number(message: str) -> str:
    """Return a container identifier from the message or a deterministic demo ID."""

    match = _CONTAINER_PATTERN.search(message)
    return match.group(0).upper() if match else "ABCU1234567"


def _extract_booking_number(message: str) -> str:
    """Return a booking identifier from the message or a deterministic demo ID."""

    match = _BOOKING_PATTERN.search(message)
    return match.group(0).upper() if match else "BK-2026-0001"


def _container_tracking_node(executor: ToolExecutor) -> Any:
    """Build the container tracking tool node."""

    def container_tracking(state: CustomerServiceState) -> dict[str, Any]:
        container_number = _extract_container_number(state["message"])
        result = executor.execute(
            _tool_request(
                state=state,
                tool_name=_TRACKING_TOOL,
                input_payload={"container_number": container_number},
            )
        )
        return {
            "tool_result": result,
            "final_answer": _format_tool_answer(result),
        }

    return container_tracking


def _booking_status_node(executor: ToolExecutor) -> Any:
    """Build the booking status tool node."""

    def booking_status(state: CustomerServiceState) -> dict[str, Any]:
        booking_number = _extract_booking_number(state["message"])
        result = executor.execute(
            _tool_request(
                state=state,
                tool_name=_BOOKING_TOOL,
                input_payload={"booking_number": booking_number},
            )
        )
        return {
            "tool_result": result,
            "final_answer": _format_tool_answer(result),
        }

    return booking_status


def _support_ticket_node(executor: ToolExecutor) -> Any:
    """Build the support ticket creation tool node."""

    def support_ticket(state: CustomerServiceState) -> dict[str, Any]:
        result = executor.execute(
            _tool_request(
                state=state,
                tool_name=_SUPPORT_TOOL,
                input_payload={
                    "customer_id": state["user_id"],
                    "subject": "Customer support request",
                    "description": state["message"],
                    "related_reference": _extract_container_number(state["message"]),
                },
            )
        )
        return {
            "tool_result": result,
            "final_answer": _format_tool_answer(result),
        }

    return support_ticket


def _format_tool_answer(result: ToolExecutionResult) -> str:
    """Return a deterministic safe answer for a tool execution result."""

    if result.status == ToolExecutionStatus.DENIED:
        return "I could not use that tool because access was denied."
    if result.status == ToolExecutionStatus.REQUIRES_APPROVAL:
        return "This action requires approval before it can continue."
    if result.status != ToolExecutionStatus.SUCCEEDED or result.output is None:
        return "I could not complete that tool request safely."

    output = result.output
    if result.tool_name == _TRACKING_TOOL:
        return (
            f"Container {output.get('container_number')} is {output.get('status')} "
            f"at {output.get('terminal')}."
        )
    if result.tool_name == _BOOKING_TOOL:
        return (
            f"Booking {output.get('booking_number')} is {output.get('status')} "
            f"with {output.get('containers_confirmed')} confirmed container(s)."
        )
    if result.tool_name == _SUPPORT_TOOL:
        return (
            f"Support ticket {output.get('ticket_id')} was {output.get('status')} "
            f"and assigned to {output.get('assigned_queue')}."
        )
    return "The tool request completed successfully."


def fallback(state: CustomerServiceState) -> dict[str, str]:
    """Return the existing deterministic hello/capability fallback."""

    return {"final_answer": state.get("final_answer") or HELLO_ANSWER}


def format_final_answer(state: CustomerServiceState) -> dict[str, Any]:
    """Normalize final answer and graph metadata before END."""

    final_answer = state.get("final_answer") or HELLO_ANSWER
    metadata = _metadata(state)
    metadata["intent"] = state.get("intent")
    metadata["safety_decision"] = state.get("safety_decision")
    grounded_answer = state.get("grounded_answer")
    if grounded_answer is not None:
        metadata["grounded"] = grounded_answer.grounded
        metadata["citation_count"] = len(grounded_answer.citations)
    tool_result = state.get("tool_result")
    if tool_result is not None:
        metadata["tool_status"] = tool_result.status.value
        metadata["tool_name"] = tool_result.tool_name

    return {
        "final_answer": final_answer,
        "handoff_required": bool(state.get("handoff_required", False)),
        "metadata": metadata,
    }


def build_graph(
    checkpointer: Any | None = None,
    *,
    safety_pipeline: SafetyPipeline | None = None,
    retriever: Retriever | None = None,
    tool_executor: ToolExecutor | None = None,
) -> Any:
    """Build the deterministic customer service demo LangGraph workflow."""

    safety_pipeline = safety_pipeline or _default_safety_pipeline()
    retriever = retriever or _default_retriever()
    tool_executor = tool_executor or _default_tool_executor()

    graph = StateGraph(CustomerServiceState)
    graph.add_node("safety_precheck", cast(Any, _safety_precheck_node(safety_pipeline)))
    graph.add_node("classify_intent", cast(Any, classify_intent_node))
    graph.add_node("rag_answer", cast(Any, _rag_answer_node(retriever)))
    graph.add_node("container_tracking", cast(Any, _container_tracking_node(tool_executor)))
    graph.add_node("booking_status", cast(Any, _booking_status_node(tool_executor)))
    graph.add_node("support_ticket", cast(Any, _support_ticket_node(tool_executor)))
    graph.add_node("fallback", cast(Any, fallback))
    graph.add_node("format_final_answer", cast(Any, format_final_answer))

    graph.set_entry_point("safety_precheck")
    graph.add_edge("safety_precheck", "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "rag_answer": "rag_answer",
            "container_tracking": "container_tracking",
            "booking_status": "booking_status",
            "support_ticket": "support_ticket",
            "fallback": "fallback",
            "format_final_answer": "format_final_answer",
        },
    )
    graph.add_edge("rag_answer", "format_final_answer")
    graph.add_edge("container_tracking", "format_final_answer")
    graph.add_edge("booking_status", "format_final_answer")
    graph.add_edge("support_ticket", "format_final_answer")
    graph.add_edge("fallback", "format_final_answer")
    graph.add_edge("format_final_answer", END)
    return graph.compile(checkpointer=checkpointer)
