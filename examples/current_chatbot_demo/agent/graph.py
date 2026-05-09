"""Reference graph shape for the current chatbot demo.

This module is documentation-oriented example code. It documents the intended
node order for the customer-service chatbot agent graph without implementing
real Qdrant retrieval, internal API calls, LLM provider calls, or runtime
registration.

Intended graph shape
--------------------
::

    input
    → safety_precheck
    → intent_routing
    → rag_branch_future_qdrant    (when intent = "rag")
    → tool_branch_future_mock_api  (when intent = "tool")
    → answer_formatting
    → runtime_response

Platform contracts used by each node (future)
----------------------------------------------
- safety_precheck:         SafetyPipeline.check_input()
- rag_branch:              Retriever.retrieve() → RetrievalResult
- tool_branch:             ToolGateway → ToolExecutor → ToolCallRecord
- answer_formatting:       CitationEnforcer (when citation policy active)

This placeholder will be replaced by a real StateGraph when PR-019 and
PR-020 land their integration adapters.
"""

from __future__ import annotations

# Ordered graph step names. Each name corresponds to a future LangGraph node.
# Nodes are listed in execution order for the RAG path; the tool path
# replaces the RAG branch step with the tool branch step.
GRAPH_STEPS = (
    "input",
    "safety_precheck",
    "intent_routing",
    "rag_branch_future_qdrant",
    "tool_branch_future_mock_api",
    "answer_formatting",
    "runtime_response",
)

# Intent values used by the intent_routing node.
INTENT_RAG = "rag"
INTENT_TOOL = "tool"
INTENT_DIRECT_ANSWER = "direct_answer"

VALID_INTENTS = frozenset({INTENT_RAG, INTENT_TOOL, INTENT_DIRECT_ANSWER})


class CurrentChatbotDemoGraph:
    """Placeholder graph object documenting the intended branch order.

    This class exists to give the ``build_graph`` entrypoint a return value
    that can be inspected in tests and documentation without requiring a real
    LangGraph compilation step.

    When promoting this agent to production, replace this class with a real
    ``langgraph.graph.StateGraph`` compiled from ``CurrentChatbotDemoState``.
    """

    def describe(self) -> tuple[str, ...]:
        """Return the documented graph step names in execution order."""
        return GRAPH_STEPS

    def valid_intents(self) -> frozenset[str]:
        """Return the set of valid routing intent values."""
        return VALID_INTENTS


def build_graph(**_kwargs: object) -> CurrentChatbotDemoGraph:
    """Build the placeholder graph for documentation and future wiring.

    This function signature matches the platform convention for graph
    entrypoints referenced in ``agent.yaml``.  Additional keyword arguments
    are accepted but ignored so that the function remains forward-compatible
    with the runtime graph loader interface.

    Returns
    -------
    CurrentChatbotDemoGraph
        A placeholder graph that documents step names without executing
        any integrations.
    """
    return CurrentChatbotDemoGraph()
