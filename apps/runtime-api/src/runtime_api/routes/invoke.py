"""LangGraph-backed invocation route for the runtime API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from runtime_api.dependencies import get_agent_registry
from runtime_api.registry import FileAgentRegistry
from snp_agent_core.contracts import RuntimeContext, RuntimeRequest, RuntimeResponse
from snp_agent_core.graph import load_graph_runner
from snp_agent_observability import build_trace_metadata

router = APIRouter(prefix="/v1/agents", tags=["invoke"])


@router.post("/{agent_id}/invoke", response_model=RuntimeResponse)
def invoke_agent(
    agent_id: str,
    request: RuntimeRequest,
    registry: Annotated[FileAgentRegistry, Depends(get_agent_registry)],
) -> RuntimeResponse:
    """Validate agent existence and invoke its manifest-declared graph."""

    manifest = registry.get_manifest(agent_id)
    context = RuntimeContext(
        request_id=f"{request.thread_id}:{agent_id}",
        tenant_id=request.tenant_id,
        channel=request.channel,
        user_id=request.user_id,
        thread_id=request.thread_id,
        agent_id=agent_id,
        metadata=request.metadata,
    )
    trace_metadata = build_trace_metadata(context=context, agent_manifest=manifest)
    runner = load_graph_runner(manifest)
    return runner.invoke(request, trace_metadata=trace_metadata)
