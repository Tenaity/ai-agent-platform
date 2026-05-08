"""Tests for policy-only ToolGateway decisions."""

from agents.customer_service.tools import CUSTOMER_SERVICE_TOOL_SPECS

from snp_agent_tools import (
    ToolAccessDecision,
    ToolAccessRequest,
    ToolExecutionMode,
    ToolGateway,
    ToolPolicy,
    ToolRegistry,
    ToolRiskLevel,
    ToolSpec,
)


def tool_spec(
    *,
    name: str = "read_resource",
    required_scopes: list[str] | None = None,
    approval_required: bool = False,
) -> ToolSpec:
    """Build a tool spec for gateway policy tests."""

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
        required_scopes=required_scopes or ["resource:read"],
        approval_required=approval_required,
    )


def access_request(
    *,
    tool_name: str = "read_resource",
    user_scopes: list[str] | None = None,
) -> ToolAccessRequest:
    """Build a tool access request for gateway tests."""

    return ToolAccessRequest(
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        tool_name=tool_name,
        user_scopes=user_scopes or ["resource:read"],
    )


def gateway_with_specs(
    specs: list[ToolSpec],
    policy: ToolPolicy,
) -> ToolGateway:
    """Build a gateway with registered specs."""

    registry = ToolRegistry()
    for spec in specs:
        registry.register(spec)
    return ToolGateway(registry=registry, policy=policy)


def test_allowed_tool_returns_allowed() -> None:
    """Allowlisted tools with required scopes are allowed."""

    gateway = gateway_with_specs(
        [tool_spec()],
        ToolPolicy(allowed_tools=["read_resource"]),
    )

    result = gateway.check_access(access_request())

    assert result.decision == ToolAccessDecision.ALLOWED
    assert result.required_scopes == ["resource:read"]
    assert result.missing_scopes == []
    assert result.approval_required is False


def test_unknown_tool_returns_denied() -> None:
    """Unknown tools are denied with a clear reason."""

    gateway = gateway_with_specs(
        [tool_spec()],
        ToolPolicy(allowed_tools=["read_resource"]),
    )

    result = gateway.check_access(access_request(tool_name="missing_tool"))

    assert result.decision == ToolAccessDecision.DENIED
    assert "not registered" in result.reason


def test_denied_tool_returns_denied() -> None:
    """Explicitly denied tools are denied even if allowlisted."""

    gateway = gateway_with_specs(
        [tool_spec()],
        ToolPolicy(
            allowed_tools=["read_resource"],
            denied_tools=["read_resource"],
        ),
    )

    result = gateway.check_access(access_request())

    assert result.decision == ToolAccessDecision.DENIED
    assert "denied by policy" in result.reason


def test_tool_not_in_allowlist_returns_default_denied() -> None:
    """Tools outside the allowlist use the policy default decision."""

    gateway = gateway_with_specs(
        [tool_spec()],
        ToolPolicy(default_decision=ToolAccessDecision.DENIED),
    )

    result = gateway.check_access(access_request())

    assert result.decision == ToolAccessDecision.DENIED
    assert "not in the policy allowlist" in result.reason


def test_missing_scope_returns_denied() -> None:
    """Allowlisted tools are denied when required scopes are missing."""

    gateway = gateway_with_specs(
        [tool_spec(required_scopes=["resource:read", "resource:audit"])],
        ToolPolicy(allowed_tools=["read_resource"]),
    )

    result = gateway.check_access(access_request(user_scopes=["resource:read"]))

    assert result.decision == ToolAccessDecision.DENIED
    assert result.required_scopes == ["resource:read", "resource:audit"]
    assert result.missing_scopes == ["resource:audit"]


def test_approval_required_tool_returns_requires_approval() -> None:
    """Tool or policy approval requirements produce requires_approval."""

    gateway = gateway_with_specs(
        [tool_spec(approval_required=True)],
        ToolPolicy(allowed_tools=["read_resource"]),
    )

    result = gateway.check_access(access_request())

    assert result.decision == ToolAccessDecision.REQUIRES_APPROVAL
    assert result.approval_required is True


def test_policy_approval_required_tool_returns_requires_approval() -> None:
    """Policy-level approval requirements are enforced."""

    gateway = gateway_with_specs(
        [tool_spec()],
        ToolPolicy(
            allowed_tools=["read_resource"],
            approval_required_tools=["read_resource"],
        ),
    )

    result = gateway.check_access(access_request())

    assert result.decision == ToolAccessDecision.REQUIRES_APPROVAL
    assert result.approval_required is True


def test_customer_service_sample_tools_can_be_checked_through_gateway() -> None:
    """Customer service sample specs work with policy-only gateway checks."""

    registry = ToolRegistry()
    for spec in CUSTOMER_SERVICE_TOOL_SPECS:
        registry.register(spec)
    gateway = ToolGateway(
        registry=registry,
        policy=ToolPolicy(
            allowed_tools=[
                "tracking_container",
                "check_booking_status",
                "create_support_ticket",
            ],
        ),
    )

    tracking_result = gateway.check_access(
        access_request(
            tool_name="tracking_container",
            user_scopes=["shipment:read"],
        )
    )
    ticket_result = gateway.check_access(
        access_request(
            tool_name="create_support_ticket",
            user_scopes=["support_ticket:write"],
        )
    )

    assert tracking_result.decision == ToolAccessDecision.ALLOWED
    assert ticket_result.decision == ToolAccessDecision.REQUIRES_APPROVAL
