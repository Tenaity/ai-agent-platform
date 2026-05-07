"""Core graph runtime abstraction."""

from typing import Any, Protocol

from snp_agent_core.contracts import AgentRunStatus, RuntimeRequest, RuntimeResponse


class InvokableGraph(Protocol):
    """Minimal graph protocol required by the core runtime runner."""

    def invoke(self, input: dict[str, Any]) -> dict[str, Any]:
        """Execute the graph with serialized state and return serialized state."""


class GraphRunner:
    """Run a compiled graph behind the stable runtime contracts.

    The runner is the boundary between framework-specific graph objects and the
    platform's `RuntimeRequest`/`RuntimeResponse` contracts. Later PRs can add
    tracing, checkpointers, safety, and tool mediation here without changing API
    route handlers.
    """

    def __init__(self, graph: InvokableGraph) -> None:
        """Create a runner around an already-built invokable graph."""

        self._graph = graph

    def invoke(self, request: RuntimeRequest) -> RuntimeResponse:
        """Execute the graph and adapt the final state into a runtime response."""

        result = self._graph.invoke(
            {
                "thread_id": request.thread_id,
                "tenant_id": request.tenant_id,
                "user_id": request.user_id,
                "channel": request.channel,
                "message": request.message,
                "final_answer": None,
            }
        )
        answer = result.get("final_answer")
        return RuntimeResponse(
            thread_id=request.thread_id,
            status=AgentRunStatus.COMPLETED,
            answer=answer if isinstance(answer, str) else None,
            citations=[],
            tool_calls=[],
            trace_id=None,
            handoff_required=False,
        )
