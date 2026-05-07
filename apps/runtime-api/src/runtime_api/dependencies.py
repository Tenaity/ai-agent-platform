"""FastAPI dependencies for runtime API routes."""

from functools import lru_cache

from runtime_api.registry.file_agent_registry import FileAgentRegistry


@lru_cache(maxsize=1)
def get_agent_registry() -> FileAgentRegistry:
    """Return the file-backed registry used by route handlers."""

    return FileAgentRegistry.from_runtime_package()
