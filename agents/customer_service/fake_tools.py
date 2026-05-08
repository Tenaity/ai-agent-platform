"""Fake customer-service tool executor for integration tests.

This module provides a deterministic, side-effect-free implementation of the
``ToolExecutor`` interface for customer-service tools. It supports the three
sample tool specs defined in ``agents/customer_service/tools.py``:

- ``tracking_container``
- ``check_booking_status``
- ``create_support_ticket``

Design constraints:
- No external API calls, network I/O, or database access of any kind.
- All outputs are deterministic given the same input, so tests can assert on
  exact values without mocking or patching.
- Unknown tool names return a safe ``failed`` result rather than raising, which
  is consistent with how ``PolicyAwareToolExecutor`` handles unexpected executor
  errors.
- Input fields are read directly from ``request.input``; validation of the
  JSON-schema contract is intentionally left to a future schema-validation layer.

This executor is domain-specific and lives in ``agents/customer_service/``.
The domain-neutral ``ToolExecutor`` interface it implements lives in
``packages/snp_agent_tools/``. That import direction (agent → package) is
explicitly allowed by the architecture rules.
"""

from snp_agent_tools import ToolExecutionRequest, ToolExecutionResult, ToolExecutionStatus
from snp_agent_tools.executor import ToolExecutor

# Fake container status data keyed by container_id.
# The deterministic mapping lets tests assert on specific field values.
_FAKE_CONTAINER_STATUS: dict[str, dict[str, str]] = {
    "CONT-001": {
        "container_id": "CONT-001",
        "status": "IN_TRANSIT",
        "last_event": "Departed port CatLai 2026-05-08T06:00:00Z",
    },
    "CONT-002": {
        "container_id": "CONT-002",
        "status": "ARRIVED",
        "last_event": "Arrived at destination port 2026-05-07T18:30:00Z",
    },
}

# Fake booking status data keyed by booking_id.
_FAKE_BOOKING_STATUS: dict[str, dict[str, str]] = {
    "BK-100": {
        "booking_id": "BK-100",
        "status": "CONFIRMED",
        "updated_at": "2026-05-01T09:00:00Z",
    },
    "BK-200": {
        "booking_id": "BK-200",
        "status": "PENDING_APPROVAL",
        "updated_at": "2026-05-06T14:00:00Z",
    },
}

# Default responses for container IDs and booking IDs not in the fake data.
_DEFAULT_CONTAINER_STATUS = "UNKNOWN"
_DEFAULT_LAST_EVENT = "No events recorded."
_DEFAULT_BOOKING_STATUS = "UNKNOWN"
_DEFAULT_BOOKING_UPDATED_AT = "N/A"


class CustomerServiceFakeToolExecutor(ToolExecutor):
    """Deterministic fake executor for customer-service tool specs.

    Supports:
    - ``tracking_container``: returns deterministic fake container status.
    - ``check_booking_status``: returns deterministic fake booking status.
    - ``create_support_ticket``: returns a deterministic fake ticket identifier.

    Unknown tool names return a ``failed`` result with a safe error message.
    No external API calls are made under any circumstances.
    """

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Dispatch to the appropriate fake handler based on tool name."""

        if request.tool_name == "tracking_container":
            return self._tracking_container(request)
        if request.tool_name == "check_booking_status":
            return self._check_booking_status(request)
        if request.tool_name == "create_support_ticket":
            return self._create_support_ticket(request)

        return ToolExecutionResult(
            tool_name=request.tool_name,
            status=ToolExecutionStatus.FAILED,
            error=f"Tool '{request.tool_name}' is not supported by this fake executor.",
        )

    def _tracking_container(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Return deterministic fake container movement milestones."""

        container_id = str(request.input.get("container_id", ""))
        fake = _FAKE_CONTAINER_STATUS.get(container_id)

        if fake:
            output = dict(fake)
        else:
            output = {
                "container_id": container_id,
                "status": _DEFAULT_CONTAINER_STATUS,
                "last_event": _DEFAULT_LAST_EVENT,
            }

        return ToolExecutionResult(
            tool_name=request.tool_name,
            status=ToolExecutionStatus.SUCCEEDED,
            output=output,
        )

    def _check_booking_status(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Return deterministic fake booking status."""

        booking_id = str(request.input.get("booking_id", ""))
        fake = _FAKE_BOOKING_STATUS.get(booking_id)

        if fake:
            output = dict(fake)
        else:
            output = {
                "booking_id": booking_id,
                "status": _DEFAULT_BOOKING_STATUS,
                "updated_at": _DEFAULT_BOOKING_UPDATED_AT,
            }

        return ToolExecutionResult(
            tool_name=request.tool_name,
            status=ToolExecutionStatus.SUCCEEDED,
            output=output,
        )

    def _create_support_ticket(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Return a deterministic fake support ticket identifier."""

        customer_id = str(request.input.get("customer_id", "UNKNOWN"))
        # Deterministic ticket ID: no randomness so tests can assert exact values.
        ticket_id = f"TICKET-{customer_id}-001"

        return ToolExecutionResult(
            tool_name=request.tool_name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={
                "ticket_id": ticket_id,
                "status": "OPEN",
            },
        )
