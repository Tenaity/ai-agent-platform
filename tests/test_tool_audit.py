"""Tests for tool call audit contracts, sinks, and executor wrapper.

Covers:
- ToolCallAuditRecord validation (required fields, UTC enforcement)
- InMemoryToolCallAuditSink record storage and retrieval
- AuditAwareToolExecutor producing audit records for succeeded and failed paths
- No stack trace leakage in audit error_summary
- Propagation of request_id, run_id, thread_id into audit records
- CustomerServiceFakeToolExecutor deterministic outputs
- Composition: PolicyAwareToolExecutor + AuditAwareToolExecutor
"""

from datetime import UTC, datetime
from typing import Any

import pytest
from agents.customer_service.fake_tools import CustomerServiceFakeToolExecutor
from pydantic import ValidationError

from snp_agent_tools import (
    AuditAwareToolExecutor,
    InMemoryToolCallAuditSink,
    PolicyAwareToolExecutor,
    ToolCallAuditRecord,
    ToolCallAuditStatus,
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
from snp_agent_tools.executor import ToolExecutor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def utc_now() -> datetime:
    """Return the current time as a UTC-aware datetime."""
    return datetime.now(UTC)


def make_request(
    *,
    tool_name: str = "tracking_container",
    input: dict[str, Any] | None = None,
    user_scopes: list[str] | None = None,
    request_id: str | None = "req-001",
    run_id: str | None = "run-001",
    thread_id: str | None = "thread-001",
) -> ToolExecutionRequest:
    """Build a sample ToolExecutionRequest for audit tests."""

    return ToolExecutionRequest(
        tool_name=tool_name,
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        input=input or {"container_id": "CONT-001"},
        user_scopes=user_scopes or ["shipment:read"],
        request_id=request_id,
        run_id=run_id,
        thread_id=thread_id,
    )


def make_tool_spec(
    *,
    name: str = "tracking_container",
    required_scopes: list[str] | None = None,
    approval_required: bool = False,
) -> ToolSpec:
    """Build a minimal ToolSpec for composition tests."""

    return ToolSpec(
        name=name,
        description="Fake tool for audit composition tests.",
        risk_level=ToolRiskLevel.LOW,
        execution_mode=ToolExecutionMode.READ,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={"type": "object", "properties": {}, "required": []},
        required_scopes=required_scopes or ["shipment:read"],
        approval_required=approval_required,
    )


def make_gateway(
    *,
    spec: ToolSpec | None = None,
    policy: ToolPolicy | None = None,
) -> ToolGateway:
    """Build a ToolGateway with one registered spec."""

    registry = ToolRegistry()
    registry.register(spec or make_tool_spec())
    return ToolGateway(
        registry=registry,
        policy=policy or ToolPolicy(allowed_tools=["tracking_container"]),
    )


# ---------------------------------------------------------------------------
# ToolCallAuditRecord validation
# ---------------------------------------------------------------------------


def test_audit_record_validates_required_fields() -> None:
    """ToolCallAuditRecord accepts all required fields when valid."""

    record = ToolCallAuditRecord(
        audit_id="audit-001",
        tool_name="tracking_container",
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        status=ToolCallAuditStatus.SUCCEEDED,
        created_at=utc_now(),
    )

    assert record.audit_id == "audit-001"
    assert record.tool_name == "tracking_container"
    assert record.status == ToolCallAuditStatus.SUCCEEDED
    assert record.created_at.tzinfo is not None


def test_audit_record_rejects_blank_audit_id() -> None:
    """Blank audit_id raises ValidationError."""

    with pytest.raises(ValidationError, match="must not be blank"):
        ToolCallAuditRecord(
            audit_id="  ",
            tool_name="tracking_container",
            agent_id="customer_service",
            tenant_id="tenant_demo",
            user_id="user_123",
            channel="api",
            status=ToolCallAuditStatus.SUCCEEDED,
            created_at=utc_now(),
        )


def test_audit_record_rejects_blank_tool_name() -> None:
    """Blank tool_name raises ValidationError."""

    with pytest.raises(ValidationError, match="must not be blank"):
        ToolCallAuditRecord(
            audit_id="audit-002",
            tool_name="",
            agent_id="customer_service",
            tenant_id="tenant_demo",
            user_id="user_123",
            channel="api",
            status=ToolCallAuditStatus.DENIED,
            created_at=utc_now(),
        )


def test_audit_record_rejects_naive_created_at() -> None:
    """Naive datetime (without tzinfo) raises ValidationError for created_at."""

    with pytest.raises(ValidationError, match="timezone-aware"):
        ToolCallAuditRecord(
            audit_id="audit-003",
            tool_name="tracking_container",
            agent_id="customer_service",
            tenant_id="tenant_demo",
            user_id="user_123",
            channel="api",
            status=ToolCallAuditStatus.SUCCEEDED,
            created_at=datetime(2026, 5, 8, 10, 0, 0),  # naive — no tzinfo
        )


def test_audit_record_created_at_is_utc_aware() -> None:
    """created_at is stored as UTC-aware and normalized to UTC."""

    record = ToolCallAuditRecord(
        audit_id="audit-004",
        tool_name="tracking_container",
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        status=ToolCallAuditStatus.SUCCEEDED,
        created_at=utc_now(),
    )

    assert record.created_at.tzinfo is not None
    assert record.created_at.utcoffset().total_seconds() == 0  # type: ignore[union-attr]


def test_audit_record_optional_fields_default_to_none() -> None:
    """Optional audit fields default to None when omitted."""

    record = ToolCallAuditRecord(
        audit_id="audit-005",
        tool_name="tracking_container",
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        status=ToolCallAuditStatus.SUCCEEDED,
        created_at=utc_now(),
    )

    assert record.request_id is None
    assert record.run_id is None
    assert record.thread_id is None
    assert record.latency_ms is None
    assert record.input_summary is None
    assert record.output_summary is None
    assert record.error_summary is None
    assert record.metadata == {}


def test_audit_record_forbids_extra_fields() -> None:
    """ToolCallAuditRecord rejects unknown fields (extra='forbid')."""

    with pytest.raises(ValidationError):
        ToolCallAuditRecord(  # type: ignore[call-arg]
            audit_id="audit-006",
            tool_name="tracking_container",
            agent_id="customer_service",
            tenant_id="tenant_demo",
            user_id="user_123",
            channel="api",
            status=ToolCallAuditStatus.SUCCEEDED,
            created_at=utc_now(),
            unexpected_field="should_fail",
        )


# ---------------------------------------------------------------------------
# InMemoryToolCallAuditSink
# ---------------------------------------------------------------------------


def test_in_memory_sink_starts_empty() -> None:
    """InMemoryToolCallAuditSink starts with no records."""

    sink = InMemoryToolCallAuditSink()
    assert sink.list_records() == []


def test_in_memory_sink_stores_records_in_insertion_order() -> None:
    """InMemoryToolCallAuditSink preserves insertion order."""

    sink = InMemoryToolCallAuditSink()

    for i in range(3):
        sink.record(
            ToolCallAuditRecord(
                audit_id=f"audit-{i:03d}",
                tool_name="tracking_container",
                agent_id="customer_service",
                tenant_id="tenant_demo",
                user_id="user_123",
                channel="api",
                status=ToolCallAuditStatus.SUCCEEDED,
                created_at=utc_now(),
            )
        )

    records = sink.list_records()
    assert len(records) == 3
    assert [r.audit_id for r in records] == ["audit-000", "audit-001", "audit-002"]


def test_in_memory_sink_list_returns_snapshot() -> None:
    """list_records() returns a copy; mutating it does not affect the sink."""

    sink = InMemoryToolCallAuditSink()
    sink.record(
        ToolCallAuditRecord(
            audit_id="audit-snap",
            tool_name="tracking_container",
            agent_id="customer_service",
            tenant_id="tenant_demo",
            user_id="user_123",
            channel="api",
            status=ToolCallAuditStatus.SUCCEEDED,
            created_at=utc_now(),
        )
    )

    snapshot = sink.list_records()
    snapshot.clear()

    assert len(sink.list_records()) == 1


# ---------------------------------------------------------------------------
# AuditAwareToolExecutor — succeeded execution
# ---------------------------------------------------------------------------


class _AlwaysSucceedExecutor(ToolExecutor):
    """Minimal executor that always returns a succeeded result."""

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=request.tool_name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={"container_id": "CONT-001", "status": "IN_TRANSIT"},
            latency_ms=10,
        )


class _AlwaysFailExecutor(ToolExecutor):
    """Minimal executor that always raises an unexpected exception."""

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        raise RuntimeError("Traceback (most recent call last): sensitive internal detail")


def test_audit_executor_records_succeeded_audit() -> None:
    """AuditAwareToolExecutor creates a succeeded audit record on success."""

    sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=_AlwaysSucceedExecutor(), audit_sink=sink)

    result = executor.execute(make_request())

    assert result.status == ToolExecutionStatus.SUCCEEDED
    records = sink.list_records()
    assert len(records) == 1
    assert records[0].status == ToolCallAuditStatus.SUCCEEDED
    assert records[0].tool_name == "tracking_container"
    assert records[0].agent_id == "customer_service"
    assert records[0].latency_ms == 10


def test_audit_executor_records_output_key_summary() -> None:
    """AuditAwareToolExecutor records output field key names, not raw values."""

    sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=_AlwaysSucceedExecutor(), audit_sink=sink)

    executor.execute(make_request())

    record = sink.list_records()[0]
    # Keys from output: container_id, status — sorted alphabetically
    assert record.output_summary is not None
    assert "container_id" in record.output_summary
    assert "status" in record.output_summary
    # Raw values must never appear in summary
    assert "CONT-001" not in (record.output_summary or "")
    assert "IN_TRANSIT" not in (record.output_summary or "")


def test_audit_executor_records_input_key_summary() -> None:
    """AuditAwareToolExecutor records input field key names, not raw values."""

    sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=_AlwaysSucceedExecutor(), audit_sink=sink)

    executor.execute(make_request(input={"container_id": "CONT-001"}))

    record = sink.list_records()[0]
    assert record.input_summary == "container_id"
    assert "CONT-001" not in (record.input_summary or "")


# ---------------------------------------------------------------------------
# AuditAwareToolExecutor — failed execution (exception from wrapped executor)
# ---------------------------------------------------------------------------


def test_audit_executor_records_failed_audit_on_exception() -> None:
    """AuditAwareToolExecutor records a failed audit when the executor raises."""

    sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=_AlwaysFailExecutor(), audit_sink=sink)

    result = executor.execute(make_request())

    assert result.status == ToolExecutionStatus.FAILED
    records = sink.list_records()
    assert len(records) == 1
    assert records[0].status == ToolCallAuditStatus.FAILED


def test_audit_executor_does_not_leak_traceback_in_error_summary() -> None:
    """error_summary must not contain stack trace or exception type details."""

    sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=_AlwaysFailExecutor(), audit_sink=sink)

    result = executor.execute(make_request())

    record = sink.list_records()[0]
    serialized = result.model_dump_json()

    # The executor raised with "Traceback ... sensitive internal detail"
    # but that must never appear in the result or the audit record.
    assert "Traceback" not in serialized
    assert "RuntimeError" not in serialized
    assert "sensitive internal detail" not in serialized

    error_summary = record.error_summary or ""
    assert "Traceback" not in error_summary
    assert "RuntimeError" not in error_summary
    assert "sensitive internal detail" not in error_summary


# ---------------------------------------------------------------------------
# AuditAwareToolExecutor — correlation identifier propagation
# ---------------------------------------------------------------------------


def test_audit_executor_propagates_request_run_thread_ids() -> None:
    """request_id, run_id, and thread_id from the request appear in the audit record."""

    sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=_AlwaysSucceedExecutor(), audit_sink=sink)

    request = make_request(
        request_id="req-propagation",
        run_id="run-propagation",
        thread_id="thread-propagation",
    )
    executor.execute(request)

    record = sink.list_records()[0]
    assert record.request_id == "req-propagation"
    assert record.run_id == "run-propagation"
    assert record.thread_id == "thread-propagation"


def test_audit_executor_handles_absent_correlation_ids() -> None:
    """Absent request_id, run_id, and thread_id are stored as None in the audit record."""

    sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=_AlwaysSucceedExecutor(), audit_sink=sink)

    request = make_request(request_id=None, run_id=None, thread_id=None)
    executor.execute(request)

    record = sink.list_records()[0]
    assert record.request_id is None
    assert record.run_id is None
    assert record.thread_id is None


# ---------------------------------------------------------------------------
# CustomerServiceFakeToolExecutor
# ---------------------------------------------------------------------------


def test_fake_executor_tracking_container_known_id() -> None:
    """tracking_container returns deterministic output for a known container ID."""

    executor = CustomerServiceFakeToolExecutor()
    request = make_request(
        tool_name="tracking_container",
        input={"container_id": "CONT-001"},
        user_scopes=["shipment:read"],
    )
    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output is not None
    assert result.output["container_id"] == "CONT-001"
    assert result.output["status"] == "IN_TRANSIT"
    assert "last_event" in result.output


def test_fake_executor_tracking_container_unknown_id() -> None:
    """tracking_container returns UNKNOWN status for an unrecognized container ID."""

    executor = CustomerServiceFakeToolExecutor()
    request = make_request(
        tool_name="tracking_container",
        input={"container_id": "CONT-UNKNOWN"},
        user_scopes=["shipment:read"],
    )
    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output is not None
    assert result.output["status"] == "UNKNOWN"


def test_fake_executor_check_booking_status_known_id() -> None:
    """check_booking_status returns deterministic output for a known booking ID."""

    executor = CustomerServiceFakeToolExecutor()
    request = make_request(
        tool_name="check_booking_status",
        input={"booking_id": "BK-100"},
        user_scopes=["booking:read"],
    )
    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output is not None
    assert result.output["booking_id"] == "BK-100"
    assert result.output["status"] == "CONFIRMED"


def test_fake_executor_check_booking_status_unknown_id() -> None:
    """check_booking_status returns UNKNOWN status for an unrecognized booking ID."""

    executor = CustomerServiceFakeToolExecutor()
    request = make_request(
        tool_name="check_booking_status",
        input={"booking_id": "BK-UNKNOWN"},
        user_scopes=["booking:read"],
    )
    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output is not None
    assert result.output["status"] == "UNKNOWN"


def test_fake_executor_create_support_ticket_deterministic() -> None:
    """create_support_ticket returns deterministic ticket ID based on customer_id."""

    executor = CustomerServiceFakeToolExecutor()
    request = make_request(
        tool_name="create_support_ticket",
        input={
            "customer_id": "CUST-42",
            "subject": "Damaged container",
            "description": "Container arrived damaged.",
        },
        user_scopes=["support_ticket:write"],
    )
    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output is not None
    assert result.output["ticket_id"] == "TICKET-CUST-42-001"
    assert result.output["status"] == "OPEN"

    # Execute again — must return the same ticket_id (deterministic).
    result2 = executor.execute(request)
    assert result2.output is not None
    assert result2.output["ticket_id"] == "TICKET-CUST-42-001"


def test_fake_executor_unknown_tool_returns_failed() -> None:
    """Unknown tool names return a failed result, not an exception."""

    executor = CustomerServiceFakeToolExecutor()
    request = make_request(
        tool_name="nonexistent_tool",
        input={},
        user_scopes=[],
    )
    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.FAILED
    assert result.error is not None
    assert "nonexistent_tool" in result.error
    assert "not supported" in result.error


# ---------------------------------------------------------------------------
# Composition: PolicyAwareToolExecutor + AuditAwareToolExecutor
# ---------------------------------------------------------------------------


def _make_composition_executor(
    *,
    policy: ToolPolicy,
    spec: ToolSpec | None = None,
) -> tuple[AuditAwareToolExecutor, InMemoryToolCallAuditSink]:
    """Build the full composition stack: Audit -> Policy -> FakeExecutor."""

    gateway = make_gateway(spec=spec, policy=policy)
    fake = CustomerServiceFakeToolExecutor()
    policy_executor = PolicyAwareToolExecutor(gateway=gateway, executor=fake)
    sink = InMemoryToolCallAuditSink()
    audit_executor = AuditAwareToolExecutor(executor=policy_executor, audit_sink=sink)
    return audit_executor, sink


def test_composition_allowed_tool_produces_succeeded_result_and_audit() -> None:
    """Allowed tool through policy produces succeeded result and succeeded audit record."""

    executor, sink = _make_composition_executor(
        policy=ToolPolicy(allowed_tools=["tracking_container"]),
    )
    request = make_request(
        tool_name="tracking_container",
        input={"container_id": "CONT-001"},
        user_scopes=["shipment:read"],
    )

    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.SUCCEEDED
    records = sink.list_records()
    assert len(records) == 1
    assert records[0].status == ToolCallAuditStatus.SUCCEEDED
    assert records[0].tool_name == "tracking_container"


def test_composition_denied_tool_produces_denied_result_and_audit() -> None:
    """Denied tool through policy produces denied result and denied audit record."""

    executor, sink = _make_composition_executor(
        policy=ToolPolicy(denied_tools=["tracking_container"]),
    )
    request = make_request(
        tool_name="tracking_container",
        input={"container_id": "CONT-001"},
        user_scopes=["shipment:read"],
    )

    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.DENIED
    records = sink.list_records()
    assert len(records) == 1
    assert records[0].status == ToolCallAuditStatus.DENIED


def test_composition_requires_approval_produces_requires_approval_result_and_audit() -> None:
    """Approval-required tool produces requires_approval result and audit record."""

    executor, sink = _make_composition_executor(
        spec=make_tool_spec(name="tracking_container", approval_required=True),
        policy=ToolPolicy(allowed_tools=["tracking_container"]),
    )
    request = make_request(
        tool_name="tracking_container",
        input={"container_id": "CONT-001"},
        user_scopes=["shipment:read"],
    )

    result = executor.execute(request)

    assert result.status == ToolExecutionStatus.REQUIRES_APPROVAL
    assert result.approval_required is True
    records = sink.list_records()
    assert len(records) == 1
    assert records[0].status == ToolCallAuditStatus.REQUIRES_APPROVAL
