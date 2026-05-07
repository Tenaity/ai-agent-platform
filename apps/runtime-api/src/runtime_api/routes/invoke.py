"""LangGraph-backed invocation route for the runtime API.

This route handler is intentionally thin. Its only responsibilities are:

1. Accept a validated HTTP POST body as a ``RuntimeRequest``.
2. Read the ``request_id`` already attached by ``RequestIdMiddleware``.
3. Delegate execution to ``InvocationService``.
4. Return the ``RuntimeResponse``.

All execution orchestration — manifest loading, run identity, timing, trace
metadata, error mapping — lives in ``InvocationService``, not here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from runtime_api.dependencies import get_invocation_service
from runtime_api.services.invocation_service import InvocationService
from snp_agent_core.contracts import RuntimeRequest, RuntimeResponse

router = APIRouter(prefix="/v1/agents", tags=["invoke"])


@router.post("/{agent_id}/invoke", response_model=RuntimeResponse)
def invoke_agent(
    agent_id: str,
    request: RuntimeRequest,
    http_request: Request,
    service: Annotated[InvocationService, Depends(get_invocation_service)],
) -> RuntimeResponse:
    """Validate agent existence and invoke its manifest-declared graph.

    The route reads ``request.state.request_id`` set by ``RequestIdMiddleware``
    and passes it through to ``InvocationService`` so the ID propagates into
    the ``AgentRun`` record and ``RuntimeResponse.metadata``.
    """

    request_id: str = getattr(http_request.state, "request_id", "")
    return service.invoke(agent_id=agent_id, request=request, request_id=request_id)
