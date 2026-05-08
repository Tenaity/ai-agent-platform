"""FastAPI dependencies for runtime API routes."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from runtime_api.registry.file_agent_registry import FileAgentRegistry
from runtime_api.services.invocation_service import InvocationService
from snp_agent_core.config.settings import Settings


@lru_cache(maxsize=1)
def get_agent_registry() -> FileAgentRegistry:
    """Return the file-backed registry used by route handlers."""

    return FileAgentRegistry.from_runtime_package()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return environment-backed runtime settings."""

    return Settings()


def get_invocation_service(
    registry: Annotated[FileAgentRegistry, Depends(get_agent_registry)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InvocationService:
    """Return an ``InvocationService`` backed by the shared agent registry.

    The service is stateless between invocations so it is safe to construct
    a new instance per request with the cached registry.
    """

    return InvocationService(registry=registry, settings=settings)
