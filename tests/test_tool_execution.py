"""Tests for tool execution contracts and policy-aware executor."""

import importlib.util
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from snp_agent_tools import (
    PolicyAwareToolExecutor,
    ToolExecutionMode,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolGateway,
    ToolPolicy,
    ToolRegistry,
    ToolRiskLevel,
    ToolSpec,
)

FAKES_PATH = (
    Path(__file__).resolve().parents[1] / "packages" / "snp_agent_tools" / "tests" / "fakes.py"
)
FAKES_SPEC = importlib.util.spec_from_file_location("snp_agent_tools_test_fakes", FAKES_PATH)
assert FAKES_SPEC is not None
assert FAKES_SPEC.loader is not None
FAKES_MODULE = importlib.util.module_from_spec(FAKES_SPEC)
FAKES_SPEC.loader.exec_module(FAKES_MODULE)
FakeToolExecutor = cast(Any, FAKES_MODULE).FakeToolExecutor


def tool_spec(
    *,
    name: str = "read_resource",
    approval_required: bool = False,
) -> ToolSpec:
    """Build a tool spec for execution tests."""

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
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
        },
        required_scopes=["resource:read"],
        approval_required=approval_required,
    )


def execution_request(
    *,
    tool_name: str = "read_resource",
    user_scopes: list[str] | None = None,
) -> ToolExecutionRequest:
    """Build a tool execution request."""

    return ToolExecutionRequest(
        tool_name=tool_name,
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        input={"resource_id": "res_123"},
        user_scopes=user_scopes or ["resource:read"],
        request_id="request_123",
        run_id="run_123",
        thread_id="thread_123",
    )


def gateway(
    *,
    spec: ToolSpec | None = None,
    policy: ToolPolicy | None = None,
) -> ToolGateway:
    """Build a gateway for execution wrapper tests."""

    registry = ToolRegistry()
    registry.register(spec or tool_spec())
    return ToolGateway(
        registry=registry,
        policy=policy or ToolPolicy(allowed_tools=["read_resource"]),
    )


def test_valid_tool_execution_request() -> None:
    """ToolExecutionRequest validates required execution context."""

    request = execution_request()

    assert request.tool_name == "read_resource"
    assert request.input == {"resource_id": "res_123"}
    assert request.request_id == "request_123"


def test_blank_tool_execution_request_name_rejected() -> None:
    """Blank execution request names are rejected."""

    with pytest.raises(ValidationError):
        execution_request(tool_name=" ")


def test_valid_tool_execution_result() -> None:
    """ToolExecutionResult validates successful output and latency."""

    result = ToolExecutionResult(
        tool_name="read_resource",
        status=ToolExecutionStatus.SUCCEEDED,
        output={"ok": True},
        latency_ms=12,
    )

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output == {"ok": True}
    assert result.latency_ms == 12


def test_denied_policy_returns_denied_result() -> None:
    """Policy denial returns a denied execution result without delegation."""

    fake = FakeToolExecutor()
    executor = PolicyAwareToolExecutor(
        gateway=gateway(policy=ToolPolicy(denied_tools=["read_resource"])),
        executor=fake,
    )

    result = executor.execute(execution_request())

    assert result.status == ToolExecutionStatus.DENIED
    assert "denied" in (result.error or "")
    assert fake.requests == []


def test_requires_approval_policy_returns_requires_approval_result() -> None:
    """Approval decisions return requires_approval without delegation."""

    fake = FakeToolExecutor()
    executor = PolicyAwareToolExecutor(
        gateway=gateway(spec=tool_spec(approval_required=True)),
        executor=fake,
    )

    result = executor.execute(execution_request())

    assert result.status == ToolExecutionStatus.REQUIRES_APPROVAL
    assert result.approval_required is True
    assert fake.requests == []


def test_allowed_policy_delegates_to_executor() -> None:
    """Allowed decisions delegate to the wrapped executor."""

    fake = FakeToolExecutor()
    executor = PolicyAwareToolExecutor(gateway=gateway(), executor=fake)

    result = executor.execute(execution_request())

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output == {"ok": True, "input": {"resource_id": "res_123"}}
    assert fake.requests == [execution_request()]


def test_executor_exception_returns_failed_result() -> None:
    """Executor exceptions are mapped to safe failed results."""

    executor = PolicyAwareToolExecutor(
        gateway=gateway(),
        executor=FakeToolExecutor(should_fail=True),
    )

    result = executor.execute(execution_request())

    assert result.status == ToolExecutionStatus.FAILED
    assert result.error == "Tool execution failed."


def test_failed_result_does_not_leak_stack_trace() -> None:
    """Failed execution results do not expose exception details or tracebacks."""

    executor = PolicyAwareToolExecutor(
        gateway=gateway(),
        executor=FakeToolExecutor(should_fail=True),
    )

    result = executor.execute(execution_request())
    serialized = result.model_dump_json()

    assert "Traceback" not in serialized
    assert "RuntimeError" not in serialized
    assert "sensitive fake stack detail" not in serialized


def test_latency_ms_is_preserved_when_executor_returns_it() -> None:
    """The policy wrapper preserves executor-reported latency."""

    executor = PolicyAwareToolExecutor(
        gateway=gateway(),
        executor=FakeToolExecutor(latency_ms=42),
    )

    result = executor.execute(execution_request())

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.latency_ms == 42
