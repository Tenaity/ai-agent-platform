"""HTTP entrypoint for the platform runtime API.

The runtime API intentionally stays thin. It should expose runtime capabilities
from reusable packages rather than embedding agent, LLM, or tool logic in route
handlers.
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from snp_agent_core.version import __version__


class HealthResponse(BaseModel):
    """Health check response used by infrastructure probes."""

    status: Literal["ok"]


class VersionResponse(BaseModel):
    """Version response for confirming the deployed platform build."""

    version: str


app = FastAPI(
    title="SNP AI Agent Platform Runtime API",
    version=__version__,
    description="Thin API facade for the internal AI Agent Platform runtime.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a lightweight readiness signal without touching downstream services."""

    return HealthResponse(status="ok")


@app.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    """Return the platform package version exposed by the core package."""

    return VersionResponse(version=__version__)
