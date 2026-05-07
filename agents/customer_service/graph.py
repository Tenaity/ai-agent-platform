"""Minimal LangGraph graph for the customer service sample agent."""

from typing import Any, cast

from langgraph.graph import END, StateGraph

from agents.customer_service.state import CustomerServiceState

HELLO_ANSWER = (
    "Hello from snp.customer_service.zalo. Real reasoning, RAG, tools, memory, "
    "and safety will be added in later PRs."
)


def generate_answer(_state: CustomerServiceState) -> dict[str, str]:
    """Return a deterministic hello answer without LLMs, tools, or external APIs."""

    return {"final_answer": HELLO_ANSWER}


def build_graph() -> Any:
    """Build the minimal customer service LangGraph workflow.

    This graph intentionally has one deterministic node. Future PRs can replace
    the node internals with reasoning, RAG, tool mediation, memory, and safety
    while preserving the manifest-declared `build_graph()` contract.
    """

    graph = StateGraph(CustomerServiceState)
    graph.add_node("generate_answer", cast(Any, generate_answer))
    graph.set_entry_point("generate_answer")
    graph.add_edge("generate_answer", END)
    return graph.compile()
