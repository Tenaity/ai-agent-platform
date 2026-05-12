"""Unit tests for the deterministic customer service demo graph."""

from agents.customer_service.graph import HELLO_ANSWER, build_graph
from agents.customer_service.intent import CustomerServiceIntent

from snp_agent_core.contracts import RuntimeRequest
from snp_agent_core.graph import GraphRunner
from snp_agent_safety import RuleBasedSafetyChecker, SafetyPipeline, SafetyPolicy
from snp_agent_tools import ToolExecutionStatus


def _state(message: str) -> dict[str, object]:
    return {
        "thread_id": "thread_456",
        "tenant_id": "tenant_demo",
        "user_id": "user_123",
        "channel": "api",
        "message": message,
        "final_answer": None,
    }


def test_unknown_question_routes_to_fallback() -> None:
    """Unknown input preserves the deterministic hello fallback for eval compatibility."""

    graph = build_graph()
    result = graph.invoke(_state("hello"))

    assert result["intent"] == CustomerServiceIntent.FALLBACK.value
    assert result["final_answer"] == HELLO_ANSWER


def test_policy_question_routes_to_rag_branch_with_citations() -> None:
    graph = build_graph()
    result = graph.invoke(_state("Cho tôi biết giờ làm việc của hỗ trợ khách hàng"))

    assert result["intent"] == CustomerServiceIntent.POLICY_QUESTION.value
    assert result["retrieval_result"].chunks
    assert result["grounded_answer"].grounded is True
    assert result["grounded_answer"].citations
    assert "08:00" in result["final_answer"]
    assert "Customer Support Opening Hours Policy" in result["final_answer"]


def test_container_query_routes_to_container_tracking_tool_branch() -> None:
    graph = build_graph()
    result = graph.invoke(_state("tracking container ABCU1234567 giúp tôi"))

    assert result["intent"] == CustomerServiceIntent.CONTAINER_TRACKING.value
    assert result["tool_result"].tool_name == "tracking_container"
    assert result["tool_result"].status == ToolExecutionStatus.SUCCEEDED
    assert "ABCU1234567" in result["final_answer"]
    assert "in_transit" in result["final_answer"]


def test_booking_query_routes_to_booking_status_tool_branch() -> None:
    graph = build_graph()
    result = graph.invoke(_state("kiểm tra booking BK-2026-0001"))

    assert result["intent"] == CustomerServiceIntent.BOOKING_STATUS.value
    assert result["tool_result"].tool_name == "check_booking_status"
    assert result["tool_result"].status == ToolExecutionStatus.SUCCEEDED
    assert "BK-2026-0001" in result["final_answer"]
    assert "confirmed" in result["final_answer"]


def test_explicit_support_ticket_routes_to_support_ticket_tool_branch() -> None:
    graph = build_graph()
    result = graph.invoke(_state("tôi muốn tạo ticket khiếu nại về dịch vụ"))

    assert result["intent"] == CustomerServiceIntent.SUPPORT_TICKET.value
    assert result["tool_result"].tool_name == "create_support_ticket"
    assert result["tool_result"].status == ToolExecutionStatus.SUCCEEDED
    assert "TICKET-user_123-001" in result["final_answer"]
    assert "created" in result["final_answer"]


def test_blocked_safety_input_does_not_execute_rag_or_tool() -> None:
    safety_pipeline = SafetyPipeline(
        [RuleBasedSafetyChecker(SafetyPolicy(blocked_terms=["blocked phrase"]))]
    )
    graph = build_graph(safety_pipeline=safety_pipeline)

    result = graph.invoke(_state("blocked phrase tracking container ABCU1234567"))

    assert result["safety_decision"] == "blocked"
    assert result["handoff_required"] is False
    assert result["final_answer"] == (
        "I cannot handle this request because it was blocked by safety policy."
    )
    assert result.get("tool_result") is None
    assert result.get("retrieval_result") is None


def test_graph_execution_works_through_graph_runner() -> None:
    runner = GraphRunner(build_graph())

    response = runner.invoke(
        RuntimeRequest(
            tenant_id="tenant_demo",
            channel="api",
            user_id="user_123",
            thread_id="thread_456",
            message="what can you do?",
        )
    )

    assert response.answer == HELLO_ANSWER
