"""Invocation service: orchestrate agent graph execution for the runtime API.

Route handlers must stay thin — they validate HTTP input and return HTTP
output. All execution orchestration belongs here so it remains testable
independently of the HTTP layer.

``InvocationService`` owns:
- manifest loading via the registry (raises ``AgentNotFoundError`` on miss)
- run identity generation (``run_id``)
- ``RuntimeContext`` construction with the real ``request_id``
- wall-clock timing around graph execution
- ``RuntimeResponse.metadata`` enrichment with lifecycle identifiers
- clean error mapping: graph failures produce a ``FAILED`` status response
  rather than leaking internal exceptions or stack traces to clients

What ``InvocationService`` deliberately does NOT own:
- persistence (future PR)
- tool mediation (future Tool Gateway PR)
- memory or RAG (future PRs)
- safety pipeline (future PR)
- real LLM calls (no model calls in the current graph)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from runtime_api.errors import AgentNotFoundError
from runtime_api.registry.file_agent_registry import FileAgentRegistry
from snp_agent_core.checkpointing import CheckpointConfig, build_checkpointer
from snp_agent_core.config.settings import Settings
from snp_agent_core.contracts import RuntimeContext, RuntimeRequest, RuntimeResponse
from snp_agent_core.contracts.runs import AgentRun, AgentRunError, AgentRunTiming
from snp_agent_core.contracts.status import AgentRunStatus
from snp_agent_core.graph import GraphLoadError, load_graph_runner
from snp_agent_observability import build_trace_metadata


class InvocationService:
    """Orchestrate a single agent graph invocation behind a stable contract.

    Instantiate once per process via the FastAPI dependency system and reuse
    across requests. The service is stateless between invocations; shared state
    lives in the registry and graph runner, both of which are safe to reuse.
    """

    def __init__(self, registry: FileAgentRegistry, settings: Settings | None = None) -> None:
        """Create the service with an already-initialised agent registry."""

        self._registry = registry
        self._settings = settings or Settings()

    def invoke(
        self,
        agent_id: str,
        request: RuntimeRequest,
        request_id: str,
    ) -> RuntimeResponse:
        """Execute an agent graph and return an enriched ``RuntimeResponse``.

        Lifecycle steps:
        1. Resolve manifest (raises ``AgentNotFoundError`` on miss).
        2. Generate a unique ``run_id`` for this execution.
        3. Build ``RuntimeContext`` with the inbound ``request_id``.
        4. Record ``started_at``.
        5. Load the graph runner (raises ``GraphLoadError`` on bad manifest).
        6. Invoke the graph.
        7. Record ``completed_at`` and compute ``duration_ms``.
        8. Return ``RuntimeResponse`` with ``run_id``, ``request_id``, and
           ``duration_ms`` in ``metadata``.

        On any graph execution exception, returns a clean ``FAILED`` response
        without exposing internal stack traces to the caller.

        Args:
            agent_id: Stable agent identifier from the URL path.
            request: Validated inbound runtime request.
            request_id: Platform-assigned request identifier from middleware.

        Returns:
            ``RuntimeResponse`` with lifecycle metadata attached.

        Raises:
            ``AgentNotFoundError``: If the agent manifest does not exist.
            ``GraphLoadError``: If the manifest-declared graph cannot be loaded.
        """

        manifest = self._registry.get_manifest(agent_id)

        run_id = str(uuid.uuid4())

        context = RuntimeContext(
            request_id=request_id,
            tenant_id=request.tenant_id,
            channel=request.channel,
            user_id=request.user_id,
            thread_id=request.thread_id,
            agent_id=agent_id,
            metadata=request.metadata,
        )

        trace_metadata = build_trace_metadata(context=context, agent_manifest=manifest)
        checkpoint_config = CheckpointConfig(
            backend=self._settings.checkpoint_backend,
            namespace=self._settings.checkpoint_namespace,
        )
        checkpointer = build_checkpointer(checkpoint_config)
        runner = load_graph_runner(
            manifest,
            checkpointer=checkpointer,
            checkpoint_namespace=checkpoint_config.namespace,
        )

        started_at = datetime.now(UTC)

        try:
            response = runner.invoke(request, trace_metadata=trace_metadata)
            completed_at = datetime.now(UTC)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            _run = AgentRun(
                run_id=run_id,
                request_id=request_id,
                agent_id=manifest.id,
                agent_version=manifest.version,
                tenant_id=request.tenant_id,
                channel=request.channel,
                user_id=request.user_id,
                thread_id=request.thread_id,
                status=response.status,
                started_at=started_at,
                completed_at=completed_at,
                timing=AgentRunTiming(total_ms=duration_ms),
                error=None,
                metadata={},
            )

            enriched_metadata: dict[str, Any] = {
                **response.metadata,
                "run_id": run_id,
                "request_id": request_id,
                "duration_ms": duration_ms,
            }
            return response.model_copy(update={"metadata": enriched_metadata})

        except (AgentNotFoundError, GraphLoadError):
            raise

        except Exception:
            completed_at = datetime.now(UTC)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            _run = AgentRun(
                run_id=run_id,
                request_id=request_id,
                agent_id=manifest.id,
                agent_version=manifest.version,
                tenant_id=request.tenant_id,
                channel=request.channel,
                user_id=request.user_id,
                thread_id=request.thread_id,
                status=AgentRunStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                timing=AgentRunTiming(total_ms=duration_ms),
                error=AgentRunError(
                    code="graph_execution_error",
                    message="Agent graph execution failed.",
                    retryable=False,
                ),
                metadata={},
            )

            return RuntimeResponse(
                thread_id=request.thread_id,
                status=AgentRunStatus.FAILED,
                answer=None,
                citations=[],
                tool_calls=[],
                trace_id=None,
                handoff_required=False,
                metadata={
                    "run_id": run_id,
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "error_code": "graph_execution_error",
                },
            )
