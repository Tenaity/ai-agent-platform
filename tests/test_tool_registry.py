"""Tests for domain-neutral tool specs and in-memory registry."""

import pytest
from agents.customer_service.tools import CUSTOMER_SERVICE_TOOL_SPECS
from pydantic import ValidationError

from snp_agent_tools import (
    DuplicateToolError,
    ToolExecutionMode,
    ToolNotFoundError,
    ToolRegistry,
    ToolRiskLevel,
    ToolSpec,
)


def valid_tool_spec(name: str = "sample_tool") -> ToolSpec:
    """Build a valid tool spec for registry tests."""

    return ToolSpec(
        name=name,
        description="Read a domain-neutral sample resource.",
        risk_level=ToolRiskLevel.LOW,
        execution_mode=ToolExecutionMode.READ,
        input_schema={
            "type": "object",
            "properties": {"resource_id": {"type": "string"}},
            "required": ["resource_id"],
        },
        output_schema={
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
        },
        required_scopes=["resource:read"],
    )


def test_valid_tool_spec_creation() -> None:
    """A complete ToolSpec validates and preserves explicit fields."""

    spec = valid_tool_spec()

    assert spec.name == "sample_tool"
    assert spec.risk_level == ToolRiskLevel.LOW
    assert spec.execution_mode == ToolExecutionMode.READ
    assert spec.approval_required is False
    assert spec.timeout_seconds == 30
    assert spec.tags == []
    assert spec.metadata == {}


def test_invalid_blank_name_rejected() -> None:
    """ToolSpec rejects blank tool names."""

    with pytest.raises(ValidationError):
        valid_tool_spec(name=" ")


def test_invalid_timeout_rejected() -> None:
    """ToolSpec rejects non-positive timeout budgets."""

    with pytest.raises(ValidationError):
        ToolSpec(
            name="bad_timeout",
            description="Invalid timeout example.",
            risk_level=ToolRiskLevel.LOW,
            execution_mode=ToolExecutionMode.READ,
            input_schema={},
            output_schema={},
            required_scopes=[],
            timeout_seconds=0,
        )


def test_registry_register_get_list_exists() -> None:
    """ToolRegistry supports basic in-memory spec lookup."""

    registry = ToolRegistry()
    spec = valid_tool_spec()

    registry.register(spec)

    assert registry.exists("sample_tool") is True
    assert registry.exists("missing_tool") is False
    assert registry.get("sample_tool") == spec
    assert registry.list() == [spec]


def test_duplicate_tool_rejected() -> None:
    """Registering the same tool name twice raises a clear error."""

    registry = ToolRegistry()
    registry.register(valid_tool_spec())

    with pytest.raises(DuplicateToolError, match="already registered"):
        registry.register(valid_tool_spec())


def test_unknown_tool_rejected() -> None:
    """Looking up an unknown tool raises a clear error."""

    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError, match="was not found"):
        registry.get("missing_tool")


def test_customer_service_sample_tools_validate() -> None:
    """Customer service sample tool specs are valid and domain-specific."""

    names = {spec.name for spec in CUSTOMER_SERVICE_TOOL_SPECS}

    assert names == {
        "tracking_container",
        "check_booking_status",
        "create_support_ticket",
    }
    assert all(isinstance(spec, ToolSpec) for spec in CUSTOMER_SERVICE_TOOL_SPECS)
    assert all(spec.required_scopes for spec in CUSTOMER_SERVICE_TOOL_SPECS)
