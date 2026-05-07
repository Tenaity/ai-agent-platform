"""LangGraph-backed invocation route for the runtime API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from runtime_api.dependencies import get_agent_registry
from runtime_api.registry import FileAgentRegistry
from snp_agent_core.contracts import RuntimeRequest, RuntimeResponse
from snp_agent_core.graph import load_graph_runner

router = APIRouter(prefix="/v1/agents", tags=["invoke"])


@router.post("/{agent_id}/invoke", response_model=RuntimeResponse)
def invoke_agent(
    agent_id: str,
    request: RuntimeRequest,
    registry: Annotated[FileAgentRegistry, Depends(get_agent_registry)],
) -> RuntimeResponse:
    """Validate agent existence and invoke its manifest-declared graph."""

    manifest = registry.get_manifest(agent_id)
    runner = load_graph_runner(manifest)
    return runner.invoke(request)
