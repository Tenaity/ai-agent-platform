"""Health and version routes for runtime API infrastructure checks."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from snp_agent_core.version import __version__


class HealthResponse(BaseModel):
    """Health check response used by infrastructure probes."""

    status: Literal["ok"]


class VersionResponse(BaseModel):
    """Version response for confirming the deployed platform build."""

    version: str


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a lightweight readiness signal without touching downstream services."""

    return HealthResponse(status="ok")


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    """Return the platform package version exposed by the core package."""

    return VersionResponse(version=__version__)
