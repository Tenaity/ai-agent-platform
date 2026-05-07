"""Scaffold invocation route for the runtime API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from runtime_api.dependencies import get_agent_registry
from runtime_api.registry import FileAgentRegistry
from snp_agent_core.contracts import AgentRunStatus, RuntimeRequest, RuntimeResponse

SCAFFOLD_ANSWER = "Runtime API scaffold is ready. Real agent execution will be added in a later PR."

router = APIRouter(prefix="/v1/agents", tags=["invoke"])


@router.post("/{agent_id}/invoke", response_model=RuntimeResponse)
def invoke_agent(
    agent_id: str,
    request: RuntimeRequest,
    registry: Annotated[FileAgentRegistry, Depends(get_agent_registry)],
) -> RuntimeResponse:
    """Validate agent existence and return a scaffold runtime response."""

    registry.get_manifest(agent_id)
    return RuntimeResponse(
        thread_id=request.thread_id,
        status=AgentRunStatus.COMPLETED,
        answer=SCAFFOLD_ANSWER,
        citations=[],
        tool_calls=[],
        trace_id=None,
        handoff_required=False,
    )
