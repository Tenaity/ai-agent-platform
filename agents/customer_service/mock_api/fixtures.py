"""Deterministic fixture data for the customer service mock APIs.

All data in this module is static and deterministic. Fixtures are keyed by the
natural identifier for each API (container number, booking number, customer ID)
so tests can assert on exact field values without patching.

Extension points
----------------
- Add new keys to the fixture dicts to cover additional test scenarios.
- Do not add randomness, timestamps from ``datetime.now()``, or external I/O.
- Do not reference real customer or company data.
"""

from __future__ import annotations

from agents.customer_service.mock_api.schemas import (
    BookingStatusData,
    ContainerEventData,
    ContainerTrackingData,
    SupportTicketData,
)

# ---------------------------------------------------------------------------
# Container tracking fixtures
# ---------------------------------------------------------------------------

CONTAINER_TRACKING_FIXTURES: dict[str, ContainerTrackingData] = {
    "ABCU1234567": ContainerTrackingData(
        container_number="ABCU1234567",
        container_type="20DC",
        status="in_transit",
        terminal="Cat Lai Terminal",
        last_event=ContainerEventData(
            event_type="gate_out",
            location="Cat Lai Terminal — Gate 3",
            timestamp="2026-05-09T08:30:00+07:00",
            description="Container departed terminal via truck",
        ),
        next_event=ContainerEventData(
            event_type="vessel_loading",
            location="Cat Lai Terminal — Berth 5",
            estimated_timestamp="2026-05-11T06:00:00+07:00",
        ),
        eta="2026-05-12",
        vessel="SNP Demo Vessel 01",
        voyage="VOY-2026-0512",
    ),
    "CONT-001": ContainerTrackingData(
        container_number="CONT-001",
        container_type="40HC",
        status="in_transit",
        terminal="Tan Cang Terminal",
        last_event=ContainerEventData(
            event_type="departed",
            location="Tan Cang Terminal",
            timestamp="2026-05-08T06:00:00+07:00",
            description="Container departed port",
        ),
        eta="2026-05-14",
        vessel="SNP Demo Vessel 02",
        voyage="VOY-2026-0514",
    ),
    "CONT-002": ContainerTrackingData(
        container_number="CONT-002",
        container_type="20DC",
        status="arrived",
        terminal="Singapore PSA",
        last_event=ContainerEventData(
            event_type="arrived",
            location="Singapore PSA",
            timestamp="2026-05-07T18:30:00+07:00",
            description="Container arrived at destination port",
        ),
        eta="2026-05-07",
        vessel="SNP Demo Vessel 01",
        voyage="VOY-2026-0507",
    ),
}

# Default response for unknown container numbers.
CONTAINER_TRACKING_DEFAULT = ContainerTrackingData(
    container_number="UNKNOWN",
    container_type="UNKNOWN",
    status="not_found",
    terminal="N/A",
    last_event=ContainerEventData(
        event_type="no_events",
        location="N/A",
        description="No tracking events recorded for this container.",
    ),
)

# ---------------------------------------------------------------------------
# Booking status fixtures
# ---------------------------------------------------------------------------

BOOKING_STATUS_FIXTURES: dict[str, BookingStatusData] = {
    "BK-2026-0001": BookingStatusData(
        booking_number="BK-2026-0001",
        status="confirmed",
        shipper="Demo Shipper Co. Ltd",
        consignee="Demo Consignee Co. Ltd",
        vessel="SNP Demo Vessel 01",
        voyage="VOY-2026-0512",
        port_of_loading="Ho Chi Minh City (Cat Lai)",
        port_of_discharge="Singapore (PSA)",
        cargo_cutoff="2026-05-10T17:00:00+07:00",
        document_cutoff="2026-05-10T12:00:00+07:00",
        containers_booked=2,
        containers_confirmed=2,
    ),
    "BK-100": BookingStatusData(
        booking_number="BK-100",
        status="confirmed",
        shipper="Test Shipper",
        consignee="Test Consignee",
        vessel="SNP Demo Vessel 02",
        voyage="VOY-2026-0514",
        port_of_loading="Ho Chi Minh City (Tan Cang)",
        port_of_discharge="Kaohsiung",
        containers_booked=1,
        containers_confirmed=1,
    ),
    "BK-200": BookingStatusData(
        booking_number="BK-200",
        status="pending_approval",
        shipper="Test Shipper 2",
        consignee="Test Consignee 2",
        containers_booked=4,
        containers_confirmed=0,
    ),
}

BOOKING_STATUS_DEFAULT = BookingStatusData(
    booking_number="UNKNOWN",
    status="not_found",
    containers_booked=0,
    containers_confirmed=0,
)

# ---------------------------------------------------------------------------
# Support ticket fixtures (created tickets, keyed by deterministic ticket_id)
# ---------------------------------------------------------------------------

# Ticket IDs are deterministic: "TICKET-{customer_id}-001"
# This matches the pattern from CustomerServiceFakeToolExecutor in fake_tools.py.

SUPPORT_TICKET_ASSIGNED_QUEUE: dict[str, str] = {
    "container": "container-ops",
    "booking": "booking-ops",
    "customs": "customs-team",
    "billing": "billing-support",
}

SUPPORT_TICKET_DEFAULTS = SupportTicketData(
    ticket_id="TICKET-UNKNOWN-001",
    status="created",
    priority="normal",
    subject="Customer service inquiry",
    assigned_queue="general-support",
    estimated_response_hours=4,
    created_at="2026-05-09T10:00:00+07:00",
)
