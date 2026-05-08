"""HTTP entrypoint for the platform runtime API."""

from fastapi import FastAPI

from runtime_api.errors import (
    AgentNotFoundError,
    agent_not_found_handler,
    graph_load_error_handler,
)
from runtime_api.middleware.request_id import RequestIdMiddleware
from runtime_api.routes import agents, health, invoke
from snp_agent_core.graph import GraphLoadError
from snp_agent_core.version import __version__


def create_app() -> FastAPI:
    """Create the FastAPI app and register route modules.

    App creation wires HTTP routes, middleware, dependencies, and exception
    handlers. Agent loading and runtime execution stay behind dedicated modules
    so route handlers remain small extension points.

    Middleware registration order matters in Starlette/FastAPI: middleware added
    later wraps earlier middleware. ``RequestIdMiddleware`` is registered first
    so the request ID is available to all downstream components including
    exception handlers.
    """

    runtime_app = FastAPI(
        title="SNP AI Agent Platform Runtime API",
        version=__version__,
        description="Thin API facade for the internal AI Agent Platform runtime.",
    )

    runtime_app.add_middleware(RequestIdMiddleware)

    runtime_app.include_router(health.router)
    runtime_app.include_router(agents.router)
    runtime_app.include_router(invoke.router)
    runtime_app.add_exception_handler(AgentNotFoundError, agent_not_found_handler)
    runtime_app.add_exception_handler(GraphLoadError, graph_load_error_handler)
    return runtime_app


app = create_app()
