"""HTTP entrypoint for the platform runtime API."""

from fastapi import FastAPI

from runtime_api.errors import (
    AgentNotFoundError,
    agent_not_found_handler,
    graph_load_error_handler,
)
from runtime_api.routes import agents, health, invoke
from snp_agent_core.graph import GraphLoadError
from snp_agent_core.version import __version__


def create_app() -> FastAPI:
    """Create the FastAPI app and register route modules.

    App creation wires HTTP routes, dependencies, and exception handlers. Agent
    loading and future runtime execution stay behind dedicated modules so route
    handlers remain small extension points.
    """

    runtime_app = FastAPI(
        title="SNP AI Agent Platform Runtime API",
        version=__version__,
        description="Thin API facade for the internal AI Agent Platform runtime.",
    )
    runtime_app.include_router(health.router)
    runtime_app.include_router(agents.router)
    runtime_app.include_router(invoke.router)
    runtime_app.add_exception_handler(AgentNotFoundError, agent_not_found_handler)
    runtime_app.add_exception_handler(GraphLoadError, graph_load_error_handler)
    return runtime_app


app = create_app()
