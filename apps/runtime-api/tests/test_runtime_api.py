"""Tests for the Runtime API shell."""

from typing import Any

from agents.customer_service.graph import HELLO_ANSWER
from fastapi.testclient import TestClient

from runtime_api.main import app
from snp_agent_core.version import __version__


def create_client() -> TestClient:
    """Create a test client for the runtime API app."""

    return TestClient(app)


def valid_runtime_request() -> dict[str, Any]:
    """Return a valid RuntimeRequest payload for invoke endpoint tests."""

    return {
        "tenant_id": "tenant_demo",
        "channel": "api",
        "user_id": "user_123",
        "thread_id": "thread_456",
        "message": "How do I reset my password?",
        "metadata": {"locale": "en-US"},
    }


def test_health_returns_ok() -> None:
    """The health endpoint returns a lightweight readiness response."""

    response = create_client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_returns_core_package_version() -> None:
    """The version endpoint exposes the core package version."""

    response = create_client().get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": __version__}


def test_list_agents_returns_customer_service_summary() -> None:
    """Agent discovery returns the sample customer service agent metadata."""

    response = create_client().get("/v1/agents")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "customer_service",
            "version": "0.1.0",
            "owner": "customer-experience-platform",
            "domain": "customer_service",
        }
    ]


def test_get_agent_manifest_returns_full_manifest() -> None:
    """The manifest endpoint returns the validated full agent manifest."""

    response = create_client().get("/v1/agents/customer_service/manifest")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "customer_service"
    assert body["runtime"]["type"] == "langgraph"
    assert body["runtime"]["graph"] == "agents.customer_service.graph:build_graph"
    assert body["memory"] is None
    assert body["retrieval"] is None
    assert body["tools"]["requires_gateway"] is True


def test_invoke_agent_returns_scaffold_response() -> None:
    """The invoke endpoint returns the customer service graph answer."""

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "thread_id": "thread_456",
        "status": "completed",
        "answer": HELLO_ANSWER,
        "citations": [],
        "tool_calls": [],
        "trace_id": None,
        "handoff_required": False,
        "metadata": {},
    }


def test_unknown_agent_returns_structured_404() -> None:
    """Unknown agent identifiers return a stable structured 404 response."""

    response = create_client().get("/v1/agents/missing/manifest")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "agent_not_found",
            "message": "Agent 'missing' was not found.",
        }
    }


def test_unknown_agent_invoke_returns_structured_404() -> None:
    """Invoke checks agent existence before returning the scaffold response."""

    response = create_client().post(
        "/v1/agents/missing/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "agent_not_found"


def test_invalid_runtime_request_returns_422() -> None:
    """FastAPI and RuntimeRequest validation reject invalid invoke payloads."""

    payload = valid_runtime_request()
    payload.pop("tenant_id")

    response = create_client().post("/v1/agents/customer_service/invoke", json=payload)

    assert response.status_code == 422
