"""Tests for the thin runtime API scaffold."""

from fastapi.testclient import TestClient

from runtime_api.main import app
from snp_agent_core.version import __version__


def test_health_returns_ok() -> None:
    """The health endpoint returns a lightweight readiness response."""

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_returns_core_package_version() -> None:
    """The version endpoint exposes the core package version."""

    client = TestClient(app)

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": __version__}
