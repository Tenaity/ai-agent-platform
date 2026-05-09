"""Tests for the Runtime API — PR-007 execution lifecycle.

Covers:
- All existing routes (health, version, agents, manifest, invoke)
- X-Request-ID middleware behaviour (generate, preserve, echo in response)
- RuntimeResponse.metadata lifecycle fields (run_id, request_id, duration_ms)
- Error cases (unknown agent 404, invalid payload 422)
- No LangSmith credentials required
"""

from collections.abc import Iterator
from typing import Any

import pytest
from agents.customer_service.graph import HELLO_ANSWER
from fastapi.testclient import TestClient

from runtime_api.dependencies import get_settings
from runtime_api.main import app
from runtime_api.registry.file_agent_registry import FileAgentRegistry
from runtime_api.services.invocation_service import InvocationService
from snp_agent_core.contracts import RuntimeRequest
from snp_agent_core.version import __version__
from snp_agent_safety import RuleBasedSafetyChecker, SafetyPipeline, SafetyPolicy


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Iterator[None]:
    """Keep environment-backed settings isolated across tests."""

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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


# ---------------------------------------------------------------------------
# Existing route tests (updated for new metadata shape)
# ---------------------------------------------------------------------------


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


def test_invoke_agent_works_without_langsmith_env(monkeypatch: Any) -> None:
    """Safe input still reaches the customer service graph answer."""

    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"] == "thread_456"
    assert body["status"] == "completed"
    assert body["answer"] == HELLO_ANSWER
    assert body["citations"] == []
    assert body["tool_calls"] == []
    assert body["trace_id"] is None
    assert body["handoff_required"] is False
    # metadata must now carry lifecycle fields (not empty)
    assert "run_id" in body["metadata"]
    assert "request_id" in body["metadata"]
    assert "duration_ms" in body["metadata"]


def test_blocked_input_returns_rejected_by_safety(monkeypatch: Any) -> None:
    """A blocking safety precheck returns before graph execution."""

    def fail_if_graph_loads(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("graph should not load after a blocked safety decision")

    monkeypatch.setattr(
        "runtime_api.services.invocation_service.load_graph_runner",
        fail_if_graph_loads,
    )

    service = InvocationService(
        registry=FileAgentRegistry.from_runtime_package(),
        safety_pipeline=SafetyPipeline(
            [RuleBasedSafetyChecker(SafetyPolicy(blocked_terms=["blocked phrase"]))]
        ),
    )
    payload = valid_runtime_request()
    payload["message"] = "This contains a blocked phrase."

    response = service.invoke(
        agent_id="customer_service",
        request=RuntimeRequest.model_validate(payload),
        request_id="safety-request-123",
    )

    assert response.status == "rejected_by_safety"
    assert response.answer is None
    assert response.metadata["request_id"] == "safety-request-123"
    assert isinstance(response.metadata["run_id"], str)
    assert isinstance(response.metadata["duration_ms"], int)
    assert response.metadata["safety_decision"] == "blocked"
    assert response.metadata["safety_flags"] == ["blocked_term"]


def test_invoke_agent_works_with_memory_checkpoint_backend(monkeypatch: Any) -> None:
    """The invoke endpoint works when in-memory checkpointing is enabled."""

    monkeypatch.setenv("SNP_CHECKPOINT_BACKEND", "memory")
    monkeypatch.setenv("SNP_CHECKPOINT_NAMESPACE", "runtime-api-test")

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"] == "thread_456"
    assert body["status"] == "completed"
    assert body["answer"] == HELLO_ANSWER
    assert "run_id" in body["metadata"]


def test_invoke_agent_does_not_return_secrets(monkeypatch: Any) -> None:
    """Runtime responses do not expose LangSmith credentials."""

    monkeypatch.setenv("LANGSMITH_API_KEY", "secret-test-key")

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 200
    assert "secret-test-key" not in response.text


def test_existing_agent_graph_execution_failure_returns_clean_failed_response(
    monkeypatch: Any,
) -> None:
    """Graph execution failures return a clean failed RuntimeResponse."""

    class FailingGraphRunner:
        def invoke(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("sensitive graph failure details")

    monkeypatch.setattr(
        "runtime_api.services.invocation_service.load_graph_runner",
        lambda *_args, **_kwargs: FailingGraphRunner(),
    )

    caller_id = "graph-failure-request-123"
    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
        headers={"X-Request-ID": caller_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"] == "thread_456"
    assert body["status"] == "failed"
    assert body["answer"] is None
    assert body["metadata"]["error_code"] == "graph_execution_error"
    assert isinstance(body["metadata"]["run_id"], str)
    assert len(body["metadata"]["run_id"]) > 0
    assert body["metadata"]["request_id"] == caller_id
    assert isinstance(body["metadata"]["duration_ms"], int)
    assert body["metadata"]["duration_ms"] >= 0
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text
    assert "sensitive graph failure details" not in response.text


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


# ---------------------------------------------------------------------------
# PR-007: X-Request-ID middleware tests
# ---------------------------------------------------------------------------


def test_request_id_is_generated_when_header_absent() -> None:
    """A UUID request_id is generated when X-Request-ID is not in the request."""

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 36  # UUID4 canonical form


def test_request_id_is_preserved_when_provided() -> None:
    """A caller-supplied X-Request-ID is preserved and echoed back unchanged."""

    caller_id = "my-gateway-request-abc123"

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
        headers={"X-Request-ID": caller_id},
    )

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == caller_id


def test_request_id_is_returned_in_response_header() -> None:
    """X-Request-ID header is always present in invoke responses."""

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert "X-Request-ID" in response.headers


def test_request_id_header_present_on_health_endpoint() -> None:
    """Middleware attaches X-Request-ID to all routes, including health."""

    response = create_client().get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers


# ---------------------------------------------------------------------------
# PR-007: RuntimeResponse metadata lifecycle fields
# ---------------------------------------------------------------------------


def test_invoke_response_metadata_contains_run_id() -> None:
    """RuntimeResponse.metadata includes a non-empty run_id string."""

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 200
    run_id = response.json()["metadata"]["run_id"]
    assert isinstance(run_id, str)
    assert len(run_id) > 0


def test_invoke_response_metadata_contains_request_id() -> None:
    """RuntimeResponse.metadata.request_id matches the response header."""

    caller_id = "correlation-xyz-456"

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
        headers={"X-Request-ID": caller_id},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["request_id"] == caller_id
    assert response.headers["X-Request-ID"] == caller_id


def test_invoke_response_metadata_contains_duration_ms() -> None:
    """RuntimeResponse.metadata.duration_ms is a non-negative integer."""

    response = create_client().post(
        "/v1/agents/customer_service/invoke",
        json=valid_runtime_request(),
    )

    assert response.status_code == 200
    duration_ms = response.json()["metadata"]["duration_ms"]
    assert isinstance(duration_ms, int)
    assert duration_ms >= 0


def test_consecutive_invocations_have_unique_run_ids() -> None:
    """Each invocation generates a distinct run_id even for identical requests."""

    client = create_client()
    payload = valid_runtime_request()

    r1 = client.post("/v1/agents/customer_service/invoke", json=payload)
    r2 = client.post("/v1/agents/customer_service/invoke", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["metadata"]["run_id"] != r2.json()["metadata"]["run_id"]
