"""ToolExecutor adapter wrapping the customer service mock API client.

``CustomerServiceMockApiToolExecutor`` implements the platform ``ToolExecutor``
interface by dispatching to ``CustomerServiceMockApiClient`` for the three
customer service tool names defined in ``agents/customer_service/tools.py``:

- ``tracking_container``
- ``check_booking_status``
- ``create_support_ticket``

Design decisions
----------------
- The mock client is injected at construction time for testability.
  Pass a custom ``CustomerServiceMockApiClient`` subclass in tests.
- ``ToolExecutionRequest.input`` is converted into typed Pydantic request
  models before calling the client.  Invalid input returns a ``failed``
  result rather than raising, consistent with the ``ToolExecutor`` contract.
- Unknown tool names return a ``failed`` result (not a raise) so the
  ``PolicyAwareToolExecutor`` safety layer is not bypassed.
- The ``tool_name`` field in ``ToolExecutionRequest`` matches the lookup
  key used by ``ToolRegistry`` — the three tool names are stable contracts.
- No external HTTP calls, database access, or secrets of any kind.
- Latency is not measured in the mock; ``latency_ms`` is left as ``None``
  unless a subclass overrides ``_measure_latency``.

Non-goals
---------
- This executor does not wire into agent graph nodes (that comes later).
- It does not audit calls (compose with ``AuditAwareToolExecutor`` for that).
- It does not enforce policy (compose with ``PolicyAwareToolExecutor``).
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from pydantic import ValidationError

from agents.customer_service.mock_api.client import CustomerServiceMockApiClient
from agents.customer_service.mock_api.schemas import (
    ApiEnvelope,
    BookingStatusRequest,
    ContainerTrackingRequest,
    SupportTicketRequest,
)
from snp_agent_tools import (
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
)
from snp_agent_tools.executor import ToolExecutor

# Stable tool name constants — must match agents/customer_service/tools.py.
_TOOL_TRACKING_CONTAINER = "tracking_container"
_TOOL_CHECK_BOOKING_STATUS = "check_booking_status"
_TOOL_CREATE_SUPPORT_TICKET = "create_support_ticket"

_SUPPORTED_TOOLS = frozenset(
    {_TOOL_TRACKING_CONTAINER, _TOOL_CHECK_BOOKING_STATUS, _TOOL_CREATE_SUPPORT_TICKET}
)


class CustomerServiceMockApiToolExecutor(ToolExecutor):
    """ToolExecutor adapter backed by the customer service mock API client.

    Dispatches ``ToolExecutionRequest`` objects to the appropriate
    ``CustomerServiceMockApiClient`` method based on ``tool_name``.

    Parameters
    ----------
    client:
        Mock API client to call.  Defaults to ``CustomerServiceMockApiClient()``.
        Pass a custom instance in tests for precise fixture control.

    Example::

        executor = CustomerServiceMockApiToolExecutor()
        request = ToolExecutionRequest(
            tool_name="tracking_container",
            agent_id="snp.customer_service.current_chatbot_demo",
            tenant_id="tenant_demo",
            user_id="user_001",
            channel="zalo",
            input={"container_number": "ABCU1234567"},
            user_scopes=["shipment:read"],
        )
        result = executor.execute(request)
        assert result.status == ToolExecutionStatus.SUCCEEDED
    """

    def __init__(
        self,
        client: CustomerServiceMockApiClient | None = None,
    ) -> None:
        """Build the executor.

        Parameters
        ----------
        client:
            ``CustomerServiceMockApiClient`` to use. Defaults to a new instance.
        """
        self._client = client or CustomerServiceMockApiClient()

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Dispatch to the appropriate mock API handler.

        Parameters
        ----------
        request:
            Validated ``ToolExecutionRequest``.

        Returns
        -------
        ToolExecutionResult
            ``succeeded`` when the mock API returns a successful envelope.
            ``failed`` when ``tool_name`` is unknown or ``input`` is invalid.
        """
        started_at = perf_counter()
        if request.tool_name == _TOOL_TRACKING_CONTAINER:
            return _with_latency(self._tracking_container(request), started_at)
        if request.tool_name == _TOOL_CHECK_BOOKING_STATUS:
            return _with_latency(self._check_booking_status(request), started_at)
        if request.tool_name == _TOOL_CREATE_SUPPORT_TICKET:
            return _with_latency(self._create_support_ticket(request), started_at)

        return _with_latency(
            ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.FAILED,
                error=(
                    f"Tool '{request.tool_name}' is not supported by "
                    f"CustomerServiceMockApiToolExecutor. "
                    f"Supported tools: {sorted(_SUPPORTED_TOOLS)}."
                ),
            ),
            started_at,
        )

    def _tracking_container(
        self, request: ToolExecutionRequest
    ) -> ToolExecutionResult:
        """Execute a container tracking request against the mock client."""

        try:
            container_number = request.input.get("container_number")
            if container_number is None:
                container_number = request.input.get("container_id", "")
            api_request = ContainerTrackingRequest(
                container_number=str(container_number),
                tenant_id=request.tenant_id,
                request_id=request.request_id,
            )
        except ValidationError as exc:
            return ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.FAILED,
                error=(
                    f"Invalid input for tracking_container: "
                    f"{exc.error_count()} validation error(s)."
                ),
            )

        envelope = self._client.track_container(api_request)
        return _envelope_to_result(request.tool_name, envelope)

    def _check_booking_status(
        self, request: ToolExecutionRequest
    ) -> ToolExecutionResult:
        """Execute a booking status request against the mock client."""

        try:
            booking_number = request.input.get("booking_number")
            if booking_number is None:
                booking_number = request.input.get("booking_id", "")
            api_request = BookingStatusRequest(
                booking_number=str(booking_number),
                tenant_id=request.tenant_id,
                request_id=request.request_id,
            )
        except ValidationError as exc:
            return ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.FAILED,
                error=(
                    f"Invalid input for check_booking_status: "
                    f"{exc.error_count()} validation error(s)."
                ),
            )

        envelope = self._client.get_booking_status(api_request)
        return _envelope_to_result(request.tool_name, envelope)

    def _create_support_ticket(
        self, request: ToolExecutionRequest
    ) -> ToolExecutionResult:
        """Execute a support ticket creation request against the mock client."""

        try:
            api_request = SupportTicketRequest(
                customer_id=str(request.input.get("customer_id", "")),
                subject=str(request.input.get("subject", "")),
                description=str(request.input.get("description", "")),
                tenant_id=request.tenant_id,
                channel=request.channel,
                priority=str(request.input.get("priority", "normal")),
                related_reference=request.input.get("related_reference"),
                request_id=request.request_id,
            )
        except ValidationError as exc:
            return ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.FAILED,
                error=(
                    f"Invalid input for create_support_ticket: "
                    f"{exc.error_count()} validation error(s)."
                ),
            )

        envelope = self._client.create_support_ticket(api_request)
        return _envelope_to_result(request.tool_name, envelope)


def _envelope_to_result(
    tool_name: str,
    envelope: ApiEnvelope[Any],
) -> ToolExecutionResult:
    """Convert an ``ApiEnvelope`` to a ``ToolExecutionResult``.

    When the envelope indicates success, serialize ``data`` to a dict.
    When it indicates failure, include the error message in the result.

    Parameters
    ----------
    tool_name:
        Tool name for the result envelope.
    envelope:
        An ``ApiEnvelope[T]`` instance.

    Returns
    -------
    ToolExecutionResult
        ``succeeded`` with serialized data, or ``failed`` with error message.
    """
    if not envelope.success:
        error_detail = envelope.error
        error_msg = (
            f"{error_detail.code}: {error_detail.message}"
            if error_detail is not None
            else "Mock API returned success=False without error details."
        )
        return ToolExecutionResult(
            tool_name=tool_name,
            status=ToolExecutionStatus.FAILED,
            error=error_msg,
        )

    data = envelope.data
    output: dict[str, Any] = data.model_dump() if data is not None else {}

    return ToolExecutionResult(
        tool_name=tool_name,
        status=ToolExecutionStatus.SUCCEEDED,
        output=output,
    )


def _with_latency(
    result: ToolExecutionResult,
    started_at: float,
) -> ToolExecutionResult:
    """Attach simple local elapsed time to a tool result."""

    latency_ms = max(0, int((perf_counter() - started_at) * 1000))
    return result.model_copy(update={"latency_ms": latency_ms})
