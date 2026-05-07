"""Agent discovery routes for the runtime API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from runtime_api.dependencies import get_agent_registry
from runtime_api.registry import AgentSummary, FileAgentRegistry
from snp_agent_core.contracts import AgentManifest

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.get("", response_model=list[AgentSummary])
def list_agents(
    registry: Annotated[FileAgentRegistry, Depends(get_agent_registry)],
) -> list[AgentSummary]:
    """Return basic metadata for registered agents."""

    return registry.list_agents()


@router.get("/{agent_id}/manifest", response_model=AgentManifest)
def get_agent_manifest(
    agent_id: str,
    registry: Annotated[FileAgentRegistry, Depends(get_agent_registry)],
) -> AgentManifest:
    """Return a validated full manifest for a registered agent."""

    return registry.get_manifest(agent_id)
