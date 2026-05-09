"""Production-like mock API client for the customer service agent.

``CustomerServiceMockApiClient`` provides deterministic, local-only
implementations of the three internal APIs used by the chatbot demo:

- Container tracking (TMS integration placeholder)
- Booking status (TMS/booking integration placeholder)
- Support ticket creation (CRM/helpdesk integration placeholder)

Design decisions
----------------
- All methods return ``ApiEnvelope[T]`` — the same structure as real APIs.
- Responses are populated from ``fixtures.py`` — no randomness, no I/O.
- Unknown identifiers return successful envelopes with a "not_found" status
  rather than raising, mirroring how real APIs behave for missing records.
- Ticket IDs are deterministic: ``TICKET-{customer_id}-001``.
- No external HTTP calls, database access, or credentials.
- The client is injected into the tool executor so tests can substitute it.

Non-goals
---------
- This client does not model authentication, retries, circuit breakers,
  or pagination.  Real adapters will add those when real APIs are wired.
"""

from agents.customer_service.mock_api.fixtures import (
    BOOKING_STATUS_FIXTURES,
    CONTAINER_TRACKING_FIXTURES,
    SUPPORT_TICKET_ASSIGNED_QUEUE,
)
from agents.customer_service.mock_api.schemas import (
    ApiEnvelope,
    BookingStatusData,
    BookingStatusRequest,
    ContainerEventData,
    ContainerTrackingData,
    ContainerTrackingRequest,
    SupportTicketData,
    SupportTicketRequest,
)

_MOCK_CREATED_AT = "2026-05-09T10:00:00+07:00"


class CustomerServiceMockApiClient:
    """Deterministic mock client for all three customer service internal APIs.

    This client is injected into ``CustomerServiceMockApiToolExecutor`` so
    the executor can be tested without any real company systems.

    Example::

        client = CustomerServiceMockApiClient()
        envelope = client.track_container(
            ContainerTrackingRequest(
                container_number="ABCU1234567",
                tenant_id="tenant_demo",
            )
        )
        print(envelope.success, envelope.data.status)
    """

    def track_container(
        self,
        request: ContainerTrackingRequest,
    ) -> ApiEnvelope[ContainerTrackingData]:
        """Return deterministic container tracking data.

        Parameters
        ----------
        request:
            Validated ``ContainerTrackingRequest`` with container number and
            tenant routing information.

        Returns
        -------
        ApiEnvelope[ContainerTrackingData]
            Always ``success=True``.  Unknown container numbers return a
            ``not_found`` status data object rather than an error envelope.
        """
        request_id = request.request_id or f"mock-tracking-{request.container_number}"
        data: ContainerTrackingData | None = CONTAINER_TRACKING_FIXTURES.get(
            request.container_number
        )

        if data is None:
            # Real APIs typically return 200 with status=not_found rather than 404
            # so calling code can distinguish "service error" from "no record".
            data = ContainerTrackingData(
                container_number=request.container_number,
                container_type="UNKNOWN",
                status="not_found",
                terminal="N/A",
                last_event=ContainerEventData(
                    event_type="no_events",
                    location="N/A",
                    description="No tracking events recorded for this container.",
                ),
            )

        return ApiEnvelope[ContainerTrackingData](
            success=True,
            data=data,
            error=None,
            request_id=request_id,
        )

    def get_booking_status(
        self,
        request: BookingStatusRequest,
    ) -> ApiEnvelope[BookingStatusData]:
        """Return deterministic booking status data.

        Parameters
        ----------
        request:
            Validated ``BookingStatusRequest`` with booking number.

        Returns
        -------
        ApiEnvelope[BookingStatusData]
            Always ``success=True``.  Unknown booking numbers return a
            ``not_found`` status data object.
        """
        request_id = request.request_id or f"mock-booking-{request.booking_number}"
        data: BookingStatusData | None = BOOKING_STATUS_FIXTURES.get(
            request.booking_number
        )

        if data is None:
            data = BookingStatusData(
                booking_number=request.booking_number,
                status="not_found",
                containers_booked=0,
                containers_confirmed=0,
            )

        return ApiEnvelope[BookingStatusData](
            success=True,
            data=data,
            error=None,
            request_id=request_id,
        )

    def create_support_ticket(
        self,
        request: SupportTicketRequest,
    ) -> ApiEnvelope[SupportTicketData]:
        """Create a deterministic support ticket.

        Ticket ID is deterministic: ``TICKET-{customer_id}-001``.
        The assigned queue is derived from subject keyword matching.

        Parameters
        ----------
        request:
            Validated ``SupportTicketRequest`` with customer and issue details.

        Returns
        -------
        ApiEnvelope[SupportTicketData]
            Always ``success=True``.
        """
        request_id = request.request_id or f"mock-ticket-{request.customer_id}"
        ticket_id = f"TICKET-{request.customer_id}-001"

        # Simple keyword-based queue assignment for the mock.
        subject_lower = request.subject.lower()
        assigned_queue = SUPPORT_TICKET_ASSIGNED_QUEUE.get("general", "general-support")
        for keyword, queue in SUPPORT_TICKET_ASSIGNED_QUEUE.items():
            if keyword in subject_lower:
                assigned_queue = queue
                break

        data = SupportTicketData(
            ticket_id=ticket_id,
            status="created",
            priority=request.priority,
            subject=request.subject,
            assigned_queue=assigned_queue,
            estimated_response_hours=4,
            created_at=_MOCK_CREATED_AT,
            customer_reference=request.related_reference,
        )

        return ApiEnvelope[SupportTicketData](
            success=True,
            data=data,
            error=None,
            request_id=request_id,
        )
