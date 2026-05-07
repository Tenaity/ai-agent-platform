"""Tests for manifest-declared graph loading."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from snp_agent_core.contracts import AgentManifest, RuntimeRequest
from snp_agent_core.graph import GraphLoadError, load_graph_runner

REPO_ROOT = Path(__file__).resolve().parents[3]
CUSTOMER_SERVICE_MANIFEST = REPO_ROOT / "agents" / "customer_service" / "agent.yaml"


def load_customer_service_manifest_data() -> dict[str, Any]:
    """Load the customer service manifest YAML for graph loader tests."""

    with CUSTOMER_SERVICE_MANIFEST.open() as manifest_file:
        loaded = yaml.safe_load(manifest_file)

    assert isinstance(loaded, dict)
    return loaded


def test_graph_loader_imports_manifest_graph() -> None:
    """The graph loader imports and runs the manifest-declared graph."""

    manifest = AgentManifest.model_validate(load_customer_service_manifest_data())
    runner = load_graph_runner(manifest)

    response = runner.invoke(
        RuntimeRequest(
            tenant_id="tenant_demo",
            channel="api",
            user_id="user_123",
            thread_id="thread_456",
            message="hello",
        )
    )

    assert response.status == "completed"
    assert response.answer is not None
    assert response.answer.startswith("Hello from snp.customer_service.zalo.")


def test_graph_loader_invalid_graph_path_raises_clear_error() -> None:
    """Invalid graph import paths raise a clear loader error."""

    data = load_customer_service_manifest_data()
    data["runtime"]["graph"] = "agents.customer_service.graph:missing_builder"
    manifest = AgentManifest.model_validate(data)

    with pytest.raises(GraphLoadError, match="does not define 'missing_builder'"):
        load_graph_runner(manifest)
