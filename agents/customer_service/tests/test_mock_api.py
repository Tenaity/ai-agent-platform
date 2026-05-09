"""Tests for the customer service mock API adapter (PR-020).

Covers:
- All Pydantic schema validation rules
- Mock API client deterministic responses for all three APIs
- ApiEnvelope structure compliance
- CustomerServiceMockApiToolExecutor dispatching for all three tools
- Invalid input returns failed ToolExecutionResult
- Unknown tool returns failed ToolExecutionResult
- No external HTTP calls or real API connections are required
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from agents.customer_service.mock_api.client import CustomerServiceMockApiClient
from agents.customer_service.mock_api.schemas import (
    ApiEnvelope,
    ApiError,
    BookingStatusData,
    BookingStatusRequest,
    ContainerTrackingData,
    ContainerTrackingRequest,
    SupportTicketData,
    SupportTicketRequest,
)
from agents.customer_service.mock_api.tool_executor import (
    CustomerServiceMockApiToolExecutor,
)
from pydantic import ValidationError

from snp_agent_tools import (
    ToolExecutionRequest,
    ToolExecutionStatus,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_request(
    tool_name: str,
    input_data: dict[str, Any],
    user_scopes: list[str] | None = None,
) -> ToolExecutionRequest:
    """Build a minimal ToolExecutionRequest for executor tests."""
    return ToolExecutionRequest(
        tool_name=tool_name,
        agent_id="snp.customer_service.current_chatbot_demo",
        tenant_id="tenant_demo",
        user_id="user_test",
        channel="api",
        input=input_data,
        user_scopes=user_scopes or ["shipment:read", "booking:read", "support_ticket:write"],
        request_id="req-test-001",
    )


# ---------------------------------------------------------------------------
# Schema tests — ApiError
# ---------------------------------------------------------------------------


_MOCK_API_SCHEMA_DIR = (
    Path(__file__).resolve().parents[3]
    / "examples"
    / "current_chatbot_demo"
    / "mock_api_schemas"
)


class TestMockApiSchemaExamples:
    def test_container_tracking_examples_validate(self) -> None:
        request_data = json.loads(
            (_MOCK_API_SCHEMA_DIR / "container_tracking.request.example.json").read_text()
        )
        response_data = json.loads(
            (_MOCK_API_SCHEMA_DIR / "container_tracking.response.example.json").read_text()
        )

        ContainerTrackingRequest.model_validate(request_data)
        ApiEnvelope[ContainerTrackingData].model_validate(response_data)

    def test_booking_status_examples_validate(self) -> None:
        request_data = json.loads(
            (_MOCK_API_SCHEMA_DIR / "booking_status.request.example.json").read_text()
        )
        response_data = json.loads(
            (_MOCK_API_SCHEMA_DIR / "booking_status.response.example.json").read_text()
        )

        BookingStatusRequest.model_validate(request_data)
        ApiEnvelope[BookingStatusData].model_validate(response_data)

    def test_support_ticket_examples_validate(self) -> None:
        request_data = json.loads(
            (_MOCK_API_SCHEMA_DIR / "support_ticket.request.example.json").read_text()
        )
        response_data = json.loads(
            (_MOCK_API_SCHEMA_DIR / "support_ticket.response.example.json").read_text()
        )

        SupportTicketRequest.model_validate(request_data)
        ApiEnvelope[SupportTicketData].model_validate(response_data)


class TestApiError:
    def test_valid_api_error_builds(self) -> None:
        err = ApiError(code="NOT_FOUND", message="Resource not found")
        assert err.code == "NOT_FOUND"
        assert err.message == "Resource not found"

    def test_blank_code_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApiError(code="  ", message="message")

    def test_blank_message_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApiError(code="ERR", message="  ")

    def test_unknown_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApiError.model_validate(
                {"code": "ERR", "message": "msg", "extra_field": "bad"}
            )


# ---------------------------------------------------------------------------
# Schema tests — ApiEnvelope
# ---------------------------------------------------------------------------


class TestApiEnvelope:
    def test_success_envelope_builds(self) -> None:
        env: ApiEnvelope[dict[str, Any]] = ApiEnvelope(
            success=True,
            data={"key": "value"},
            error=None,
            request_id="req-001",
        )
        assert env.success is True
        assert env.data == {"key": "value"}
        assert env.error is None

    def test_failure_envelope_builds(self) -> None:
        env: ApiEnvelope[dict[str, Any]] = ApiEnvelope(
            success=False,
            data=None,
            error=ApiError(code="ERR_001", message="Something failed"),
            request_id="req-002",
        )
        assert env.success is False
        assert env.error is not None
        assert env.error.code == "ERR_001"

    def test_blank_request_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApiEnvelope(success=True, data=None, error=None, request_id="  ")

    def test_unknown_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            # Pydantic extra=forbid will reject this
            ApiEnvelope.model_validate(
                {
                    "success": True,
                    "data": None,
                    "error": None,
                    "request_id": "req",
                    "bad_field": "x",
                }
            )


# ---------------------------------------------------------------------------
# Schema tests — ContainerTrackingRequest
# ---------------------------------------------------------------------------


class TestContainerTrackingRequest:
    def test_valid_request_builds(self) -> None:
        req = ContainerTrackingRequest(
            container_number="ABCU1234567", tenant_id="tenant_demo"
        )
        assert req.container_number == "ABCU1234567"
        assert req.tenant_id == "tenant_demo"
        assert req.request_id is None

    def test_blank_container_number_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ContainerTrackingRequest(container_number="  ", tenant_id="tenant_demo")

    def test_blank_tenant_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ContainerTrackingRequest(container_number="CONT-001", tenant_id="  ")

    def test_optional_request_id_can_be_set(self) -> None:
        req = ContainerTrackingRequest(
            container_number="CONT-001", tenant_id="t", request_id="rid-001"
        )
        assert req.request_id == "rid-001"


# ---------------------------------------------------------------------------
# Schema tests — BookingStatusRequest
# ---------------------------------------------------------------------------


class TestBookingStatusRequest:
    def test_valid_request_builds(self) -> None:
        req = BookingStatusRequest(
            booking_number="BK-2026-0001", tenant_id="tenant_demo"
        )
        assert req.booking_number == "BK-2026-0001"

    def test_blank_booking_number_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BookingStatusRequest(booking_number="", tenant_id="tenant_demo")


# ---------------------------------------------------------------------------
# Schema tests — SupportTicketRequest
# ---------------------------------------------------------------------------


class TestSupportTicketRequest:
    def test_valid_request_builds(self) -> None:
        req = SupportTicketRequest(
            customer_id="customer_123",
            subject="Container issue",
            description="Container ABCU1234567 has no update.",
            tenant_id="tenant_demo",
        )
        assert req.customer_id == "customer_123"
        assert req.priority == "normal"
        assert req.channel == "api"

    def test_blank_customer_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SupportTicketRequest(
                customer_id="  ",
                subject="s",
                description="d",
                tenant_id="t",
            )

    def test_blank_subject_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SupportTicketRequest(
                customer_id="c",
                subject="  ",
                description="d",
                tenant_id="t",
            )

    def test_blank_description_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SupportTicketRequest(
                customer_id="c",
                subject="s",
                description="  ",
                tenant_id="t",
            )

    def test_related_reference_is_optional(self) -> None:
        req = SupportTicketRequest(
            customer_id="c",
            subject="s",
            description="d",
            tenant_id="t",
            related_reference="ABCU1234567",
        )
        assert req.related_reference == "ABCU1234567"


# ---------------------------------------------------------------------------
# Mock API client — container tracking
# ---------------------------------------------------------------------------


class TestMockApiClientContainerTracking:
    def _client(self) -> CustomerServiceMockApiClient:
        return CustomerServiceMockApiClient()

    def test_known_container_returns_success(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="ABCU1234567", tenant_id="tenant_demo"
            )
        )
        assert env.success is True
        assert env.error is None
        assert isinstance(env.data, ContainerTrackingData)

    def test_known_container_returns_correct_status(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="ABCU1234567", tenant_id="tenant_demo"
            )
        )
        assert env.data is not None
        assert env.data.status == "in_transit"
        assert env.data.container_number == "ABCU1234567"

    def test_known_container_has_vessel_and_voyage(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="ABCU1234567", tenant_id="tenant_demo"
            )
        )
        assert env.data is not None
        assert env.data.vessel == "SNP Demo Vessel 01"
        assert env.data.voyage == "VOY-2026-0512"

    def test_known_container_has_last_event(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="ABCU1234567", tenant_id="tenant_demo"
            )
        )
        assert env.data is not None
        assert env.data.last_event.event_type == "gate_out"

    def test_unknown_container_returns_not_found_status(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="CONT-UNKNOWN-999", tenant_id="tenant_demo"
            )
        )
        assert env.success is True
        assert env.data is not None
        assert env.data.status == "not_found"

    def test_unknown_container_echoes_container_number(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="CONT-UNKNOWN-999", tenant_id="tenant_demo"
            )
        )
        assert env.data is not None
        assert env.data.container_number == "CONT-UNKNOWN-999"

    def test_request_id_is_preserved(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="ABCU1234567",
                tenant_id="tenant_demo",
                request_id="my-req-id",
            )
        )
        assert env.request_id == "my-req-id"

    def test_arrived_container_returns_correct_status(self) -> None:
        env = self._client().track_container(
            ContainerTrackingRequest(
                container_number="CONT-002", tenant_id="tenant_demo"
            )
        )
        assert env.data is not None
        assert env.data.status == "arrived"

    def test_response_is_deterministic(self) -> None:
        client = self._client()
        req = ContainerTrackingRequest(
            container_number="ABCU1234567", tenant_id="tenant_demo"
        )
        result1 = client.track_container(req)
        result2 = client.track_container(req)
        assert result1.data == result2.data


# ---------------------------------------------------------------------------
# Mock API client — booking status
# ---------------------------------------------------------------------------


class TestMockApiClientBookingStatus:
    def _client(self) -> CustomerServiceMockApiClient:
        return CustomerServiceMockApiClient()

    def test_known_booking_returns_success(self) -> None:
        env = self._client().get_booking_status(
            BookingStatusRequest(
                booking_number="BK-2026-0001", tenant_id="tenant_demo"
            )
        )
        assert env.success is True
        assert isinstance(env.data, BookingStatusData)

    def test_known_booking_returns_correct_status(self) -> None:
        env = self._client().get_booking_status(
            BookingStatusRequest(
                booking_number="BK-2026-0001", tenant_id="tenant_demo"
            )
        )
        assert env.data is not None
        assert env.data.status == "confirmed"
        assert env.data.containers_booked == 2
        assert env.data.containers_confirmed == 2

    def test_known_booking_has_cutoff_dates(self) -> None:
        env = self._client().get_booking_status(
            BookingStatusRequest(
                booking_number="BK-2026-0001", tenant_id="tenant_demo"
            )
        )
        assert env.data is not None
        assert env.data.cargo_cutoff is not None
        assert env.data.document_cutoff is not None

    def test_pending_booking_returns_pending_status(self) -> None:
        env = self._client().get_booking_status(
            BookingStatusRequest(booking_number="BK-200", tenant_id="tenant_demo")
        )
        assert env.data is not None
        assert env.data.status == "pending_approval"

    def test_unknown_booking_returns_not_found_status(self) -> None:
        env = self._client().get_booking_status(
            BookingStatusRequest(
                booking_number="BK-DOES-NOT-EXIST", tenant_id="tenant_demo"
            )
        )
        assert env.success is True
        assert env.data is not None
        assert env.data.status == "not_found"

    def test_response_is_deterministic(self) -> None:
        client = self._client()
        req = BookingStatusRequest(
            booking_number="BK-2026-0001", tenant_id="tenant_demo"
        )
        result1 = client.get_booking_status(req)
        result2 = client.get_booking_status(req)
        assert result1.data == result2.data


# ---------------------------------------------------------------------------
# Mock API client — support ticket
# ---------------------------------------------------------------------------


class TestMockApiClientSupportTicket:
    def _client(self) -> CustomerServiceMockApiClient:
        return CustomerServiceMockApiClient()

    def test_creates_support_ticket_successfully(self) -> None:
        env = self._client().create_support_ticket(
            SupportTicketRequest(
                customer_id="customer_123",
                subject="Container tracking missing",
                description="No update for ABCU1234567.",
                tenant_id="tenant_demo",
            )
        )
        assert env.success is True
        assert isinstance(env.data, SupportTicketData)

    def test_ticket_id_is_deterministic(self) -> None:
        env = self._client().create_support_ticket(
            SupportTicketRequest(
                customer_id="customer_123",
                subject="Test subject",
                description="Test description.",
                tenant_id="tenant_demo",
            )
        )
        assert env.data is not None
        assert env.data.ticket_id == "TICKET-customer_123-001"

    def test_ticket_status_is_created(self) -> None:
        env = self._client().create_support_ticket(
            SupportTicketRequest(
                customer_id="customer_123",
                subject="Test subject",
                description="Test description.",
                tenant_id="tenant_demo",
            )
        )
        assert env.data is not None
        assert env.data.status == "created"

    def test_ticket_priority_from_request(self) -> None:
        env = self._client().create_support_ticket(
            SupportTicketRequest(
                customer_id="cust_001",
                subject="Urgent container issue",
                description="Container stuck.",
                tenant_id="tenant_demo",
                priority="high",
            )
        )
        assert env.data is not None
        assert env.data.priority == "high"

    def test_related_reference_echoed(self) -> None:
        env = self._client().create_support_ticket(
            SupportTicketRequest(
                customer_id="cust_001",
                subject="Tracking issue",
                description="No update for container.",
                tenant_id="tenant_demo",
                related_reference="ABCU1234567",
            )
        )
        assert env.data is not None
        assert env.data.customer_reference == "ABCU1234567"

    def test_ticket_creation_is_deterministic(self) -> None:
        client = self._client()
        req = SupportTicketRequest(
            customer_id="cust_001",
            subject="s",
            description="d",
            tenant_id="t",
        )
        result1 = client.create_support_ticket(req)
        result2 = client.create_support_ticket(req)
        assert result1.data == result2.data


# ---------------------------------------------------------------------------
# Tool executor — tracking_container
# ---------------------------------------------------------------------------


class TestMockApiToolExecutorTrackingContainer:
    def _executor(self) -> CustomerServiceMockApiToolExecutor:
        return CustomerServiceMockApiToolExecutor()

    def test_tracking_container_returns_succeeded(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "tracking_container",
                {"container_number": "ABCU1234567"},
            )
        )
        assert result.status == ToolExecutionStatus.SUCCEEDED

    def test_tracking_container_output_has_status(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "tracking_container",
                {"container_number": "ABCU1234567"},
            )
        )
        assert result.output is not None
        assert result.output["status"] == "in_transit"

    def test_tracking_container_output_has_vessel(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "tracking_container",
                {"container_number": "ABCU1234567"},
            )
        )
        assert result.output is not None
        assert result.output["vessel"] == "SNP Demo Vessel 01"

    def test_tracking_unknown_container_returns_succeeded_not_found(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "tracking_container",
                {"container_number": "CONT-DOES-NOT-EXIST"},
            )
        )
        assert result.status == ToolExecutionStatus.SUCCEEDED
        assert result.output is not None
        assert result.output["status"] == "not_found"

    def test_tracking_container_blank_number_returns_failed(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "tracking_container",
                {"container_number": "  "},
            )
        )
        assert result.status == ToolExecutionStatus.FAILED
        assert "Invalid input" in (result.error or "")

    def test_tracking_container_missing_field_returns_failed(self) -> None:
        result = self._executor().execute(
            _tool_request("tracking_container", {})
        )
        assert result.status == ToolExecutionStatus.FAILED
        assert result.error is not None


# ---------------------------------------------------------------------------
# Tool executor — check_booking_status
# ---------------------------------------------------------------------------


class TestMockApiToolExecutorBookingStatus:
    def _executor(self) -> CustomerServiceMockApiToolExecutor:
        return CustomerServiceMockApiToolExecutor()

    def test_booking_status_returns_succeeded(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "check_booking_status",
                {"booking_number": "BK-2026-0001"},
            )
        )
        assert result.status == ToolExecutionStatus.SUCCEEDED

    def test_booking_status_output_has_status(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "check_booking_status",
                {"booking_number": "BK-2026-0001"},
            )
        )
        assert result.output is not None
        assert result.output["status"] == "confirmed"

    def test_booking_status_output_has_containers_confirmed(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "check_booking_status",
                {"booking_number": "BK-2026-0001"},
            )
        )
        assert result.output is not None
        assert result.output["containers_confirmed"] == 2

    def test_unknown_booking_returns_not_found(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "check_booking_status",
                {"booking_number": "BK-DOES-NOT-EXIST"},
            )
        )
        assert result.status == ToolExecutionStatus.SUCCEEDED
        assert result.output is not None
        assert result.output["status"] == "not_found"

    def test_blank_booking_number_returns_failed(self) -> None:
        result = self._executor().execute(
            _tool_request("check_booking_status", {"booking_number": "  "})
        )
        assert result.status == ToolExecutionStatus.FAILED


# ---------------------------------------------------------------------------
# Tool executor — create_support_ticket
# ---------------------------------------------------------------------------


class TestMockApiToolExecutorSupportTicket:
    def _executor(self) -> CustomerServiceMockApiToolExecutor:
        return CustomerServiceMockApiToolExecutor()

    def test_create_support_ticket_returns_succeeded(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "create_support_ticket",
                {
                    "customer_id": "customer_123",
                    "subject": "Container tracking missing",
                    "description": "No update for ABCU1234567.",
                },
            )
        )
        assert result.status == ToolExecutionStatus.SUCCEEDED

    def test_create_support_ticket_output_has_ticket_id(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "create_support_ticket",
                {
                    "customer_id": "customer_123",
                    "subject": "Container tracking missing",
                    "description": "No update.",
                },
            )
        )
        assert result.output is not None
        assert result.output["ticket_id"] == "TICKET-customer_123-001"

    def test_create_support_ticket_output_has_created_status(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "create_support_ticket",
                {
                    "customer_id": "cust_001",
                    "subject": "Booking issue",
                    "description": "Booking BK-100 missing containers.",
                },
            )
        )
        assert result.output is not None
        assert result.output["status"] == "created"

    def test_blank_customer_id_returns_failed(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "create_support_ticket",
                {"customer_id": "  ", "subject": "s", "description": "d"},
            )
        )
        assert result.status == ToolExecutionStatus.FAILED

    def test_blank_subject_returns_failed(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "create_support_ticket",
                {"customer_id": "c", "subject": "  ", "description": "d"},
            )
        )
        assert result.status == ToolExecutionStatus.FAILED

    def test_blank_description_returns_failed(self) -> None:
        result = self._executor().execute(
            _tool_request(
                "create_support_ticket",
                {"customer_id": "c", "subject": "s", "description": "  "},
            )
        )
        assert result.status == ToolExecutionStatus.FAILED


# ---------------------------------------------------------------------------
# Tool executor — unknown tool
# ---------------------------------------------------------------------------


class TestMockApiToolExecutorUnknownTool:
    def test_unknown_tool_returns_failed(self) -> None:
        result = CustomerServiceMockApiToolExecutor().execute(
            _tool_request("nonexistent_tool", {"key": "value"})
        )
        assert result.status == ToolExecutionStatus.FAILED

    def test_unknown_tool_error_mentions_tool_name(self) -> None:
        result = CustomerServiceMockApiToolExecutor().execute(
            _tool_request("nonexistent_tool", {"key": "value"})
        )
        assert "nonexistent_tool" in (result.error or "")

    def test_unknown_tool_error_lists_supported_tools(self) -> None:
        result = CustomerServiceMockApiToolExecutor().execute(
            _tool_request("does_not_exist", {})
        )
        error = result.error or ""
        assert "tracking_container" in error or "Supported tools" in error

    def test_tool_name_preserved_in_failed_result(self) -> None:
        result = CustomerServiceMockApiToolExecutor().execute(
            _tool_request("bad_tool", {})
        )
        assert result.tool_name == "bad_tool"


# ---------------------------------------------------------------------------
# Tool executor — no real HTTP calls
# ---------------------------------------------------------------------------


class TestMockApiNoRealHttpCalls:
    """Verify mock uses no real HTTP at all — even when requests is available."""

    def test_executor_does_not_import_requests_or_httpx(self) -> None:
        """The mock client module must not import requests or httpx at module level."""
        import importlib
        import sys

        # Reload the client module and verify no HTTP libraries are auto-imported
        # by checking sys.modules for telltale network libraries.
        before = set(sys.modules.keys())
        importlib.import_module("agents.customer_service.mock_api.client")
        after = set(sys.modules.keys())
        new_modules = after - before
        # Should not pull in real HTTP clients.
        assert "requests" not in new_modules
        assert "httpx" not in new_modules
        assert "urllib3" not in new_modules

    def test_all_three_tools_produce_results_without_network(self) -> None:
        """All three tools return results from memory without network access."""
        executor = CustomerServiceMockApiToolExecutor()

        r1 = executor.execute(
            _tool_request("tracking_container", {"container_number": "ABCU1234567"})
        )
        r2 = executor.execute(
            _tool_request("check_booking_status", {"booking_number": "BK-2026-0001"})
        )
        r3 = executor.execute(
            _tool_request(
                "create_support_ticket",
                {
                    "customer_id": "c",
                    "subject": "s",
                    "description": "d",
                },
            )
        )
        assert r1.status == ToolExecutionStatus.SUCCEEDED
        assert r2.status == ToolExecutionStatus.SUCCEEDED
        assert r3.status == ToolExecutionStatus.SUCCEEDED
