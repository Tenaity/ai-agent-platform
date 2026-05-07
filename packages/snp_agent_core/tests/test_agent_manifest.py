"""Tests for the typed agent manifest contract."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from snp_agent_core.contracts.agent_manifest import AgentManifest

REPO_ROOT = Path(__file__).resolve().parents[3]
CUSTOMER_SERVICE_MANIFEST = REPO_ROOT / "agents" / "customer_service" / "agent.yaml"


def load_customer_service_manifest() -> dict[str, Any]:
    """Load the sample customer service manifest from disk."""

    with CUSTOMER_SERVICE_MANIFEST.open() as manifest_file:
        loaded = yaml.safe_load(manifest_file)

    assert isinstance(loaded, dict)
    return loaded


def test_sample_customer_service_manifest_validates() -> None:
    """The sample agent manifest validates against the public contract."""

    manifest = AgentManifest.model_validate(load_customer_service_manifest())

    assert manifest.id == "customer_service"
    assert manifest.tools.requires_gateway is True
    assert manifest.model_policy.allow_real_calls is False


def test_agent_manifest_rejects_blank_required_identity_fields() -> None:
    """Blank identity fields are rejected before manifests enter runtime code."""

    data = load_customer_service_manifest()
    data["id"] = " "

    with pytest.raises(ValidationError):
        AgentManifest.model_validate(data)


def test_agent_manifest_rejects_unknown_keys() -> None:
    """Unexpected manifest keys are rejected to keep the YAML contract explicit."""

    data = load_customer_service_manifest()
    data["unexpected"] = "value"

    with pytest.raises(ValidationError):
        AgentManifest.model_validate(data)
