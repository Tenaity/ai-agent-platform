"""Tests for trace metadata construction."""

from snp_agent_core.contracts import AgentManifest, RuntimeContext
from snp_agent_observability import build_trace_metadata


def test_build_trace_metadata_includes_platform_context() -> None:
    """Trace metadata includes stable runtime and agent ownership fields."""

    context = RuntimeContext(
        request_id="request_123",
        tenant_id="tenant_demo",
        channel="api",
        user_id="user_123",
        thread_id="thread_456",
        agent_id="customer_service",
    )
    manifest = AgentManifest.model_validate(
        {
            "id": "customer_service",
            "version": "0.1.0",
            "owner": "customer-experience-platform",
            "domain": "customer_service",
            "runtime": {
                "type": "langgraph",
                "graph": "agents.customer_service.graph:build_graph",
                "state_schema": "agents.customer_service.state:CustomerServiceState",
            },
            "model_policy": {
                "provider": "none",
                "model": "placeholder",
                "allow_real_calls": False,
            },
            "memory": None,
            "retrieval": None,
            "tools": {"allowed": [], "requires_gateway": True},
            "safety": {"policy": "default_customer_support", "human_review_required": True},
            "observability": {"tracing": True, "project": "customer_service"},
            "eval": {"dataset": "datasets/customer_service", "min_pass_rate": 0.9},
        }
    )

    assert build_trace_metadata(context=context, agent_manifest=manifest) == {
        "request_id": "request_123",
        "tenant_id": "tenant_demo",
        "channel": "api",
        "user_id": "user_123",
        "thread_id": "thread_456",
        "agent_id": "customer_service",
        "agent_version": "0.1.0",
        "domain": "customer_service",
    }
