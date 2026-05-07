"""Unit tests for the customer service LangGraph sample."""

from agents.customer_service.graph import HELLO_ANSWER, build_graph


def test_customer_service_graph_generates_hello_answer() -> None:
    """The sample graph returns the deterministic PR-004 hello answer."""

    graph = build_graph()

    result = graph.invoke(
        {
            "thread_id": "thread_456",
            "tenant_id": "tenant_demo",
            "user_id": "user_123",
            "channel": "api",
            "message": "hello",
            "final_answer": None,
        }
    )

    assert result["final_answer"] == HELLO_ANSWER
