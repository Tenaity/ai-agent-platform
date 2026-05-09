"""Reference graph shape for the current chatbot demo.

This file is documentation-oriented example code. It does not call Qdrant,
internal APIs, LLM providers, or the runtime service.
"""

from __future__ import annotations

GRAPH_STEPS = (
    "input",
    "safety_precheck",
    "intent_routing",
    "rag_branch_future_qdrant",
    "tool_branch_future_mock_api",
    "answer_formatting",
    "runtime_response",
)


class CurrentChatbotDemoGraph:
    """Placeholder graph object showing the intended branch order."""

    def describe(self) -> tuple[str, ...]:
        """Return the documented graph steps without executing integrations."""

        return GRAPH_STEPS


def build_graph(**_kwargs: object) -> CurrentChatbotDemoGraph:
    """Build the placeholder graph for documentation and future wiring."""

    return CurrentChatbotDemoGraph()

