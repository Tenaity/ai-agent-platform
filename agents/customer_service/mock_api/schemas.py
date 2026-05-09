"""Production-like Pydantic schemas for the customer service mock APIs.

These schemas mirror the structure of the real internal APIs documented in
``examples/current_chatbot_demo/mock_api_schemas/``.  Using Pydantic models
instead of plain dicts ensures that:

- Request construction is validated at test time.
- Response envelopes are typed and safe to pass across module boundaries.
- The mock client has an explicit contract reviewers can inspect.

Design rules
------------
- No real API calls, credentials, or network I/O.
- ``extra="forbid"`` on all models so unintended fields fail fast.
- ``Generic[T]`` envelope keeps response typing correct without duplication.
- All optional fields default to ``None`` for forward compatibility.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class MockApiBaseModel(BaseModel):
    """Base model for all mock API contracts: rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


class ApiError(MockApiBaseModel):
    """Error detail returned when success=False."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")

    @field_validator("code", "message")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        """Reject blank error fields."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class ApiEnvelope(MockApiBaseModel, Generic[T]):
    """Production-like API response envelope.

    Matches the structure documented in
    ``examples/current_chatbot_demo/mock_api_schemas/*.response.example.json``:

    .. code-block:: json

        {
            "success": true,
            "data": { ... },
            "error": null,
            "request_id": "mock-request-id"
        }

    Invariants
    ----------
    - When ``success=True``, ``data`` is set and ``error`` is ``None``.
    - When ``success=False``, ``error`` is set and ``data`` may be ``None``.
    - ``request_id`` is always provided for correlation.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    success: bool = Field(..., description="Whether the API call succeeded.")
    data: T | None = Field(default=None, description="Response payload when success=True.")
    error: ApiError | None = Field(default=None, description="Error detail when success=False.")
    request_id: str = Field(..., description="Request correlation identifier.")

    @field_validator("request_id")
    @classmethod
    def reject_blank_request_id(cls, value: str) -> str:
        """Reject blank request IDs."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("request_id must not be blank")
        return stripped


# ---------------------------------------------------------------------------
# Container tracking
# ---------------------------------------------------------------------------


class ContainerTrackingRequest(MockApiBaseModel):
    """Input for the container tracking API."""

    container_number: str = Field(
        ...,
        description="Container identifier (e.g. ABCU1234567).",
    )
    tenant_id: str = Field(..., description="Tenant routing identifier.")
    request_id: str | None = Field(default=None, description="Optional correlation ID.")

    @field_validator("container_number", "tenant_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        """Reject blank required fields."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class ContainerEventData(MockApiBaseModel):
    """A single container event milestone."""

    event_type: str = Field(..., description="Event type code (e.g. gate_out).")
    location: str = Field(..., description="Location description.")
    timestamp: str | None = Field(default=None, description="Actual event timestamp (ISO 8601).")
    estimated_timestamp: str | None = Field(
        default=None,
        description="Estimated event timestamp (ISO 8601).",
    )
    description: str | None = Field(default=None, description="Human-readable event description.")


class ContainerTrackingData(MockApiBaseModel):
    """Response payload for the container tracking API."""

    container_number: str = Field(..., description="Container identifier.")
    container_type: str = Field(..., description="Container size/type code (e.g. 20DC).")
    status: str = Field(..., description="Current container status.")
    terminal: str = Field(..., description="Current or last terminal.")
    last_event: ContainerEventData = Field(..., description="Most recent tracking event.")
    next_event: ContainerEventData | None = Field(
        default=None,
        description="Next expected event.",
    )
    eta: str | None = Field(default=None, description="Estimated time of arrival (YYYY-MM-DD).")
    vessel: str | None = Field(default=None, description="Vessel name.")
    voyage: str | None = Field(default=None, description="Voyage identifier.")


# ---------------------------------------------------------------------------
# Booking status
# ---------------------------------------------------------------------------


class BookingStatusRequest(MockApiBaseModel):
    """Input for the booking status API."""

    booking_number: str = Field(..., description="Booking reference number.")
    tenant_id: str = Field(..., description="Tenant routing identifier.")
    request_id: str | None = Field(default=None, description="Optional correlation ID.")

    @field_validator("booking_number", "tenant_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        """Reject blank required fields."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class BookingStatusData(MockApiBaseModel):
    """Response payload for the booking status API."""

    booking_number: str = Field(..., description="Booking reference number.")
    status: str = Field(..., description="Current booking status.")
    shipper: str | None = Field(default=None, description="Shipper name.")
    consignee: str | None = Field(default=None, description="Consignee name.")
    vessel: str | None = Field(default=None, description="Vessel name.")
    voyage: str | None = Field(default=None, description="Voyage identifier.")
    port_of_loading: str | None = Field(default=None, description="Port of loading.")
    port_of_discharge: str | None = Field(default=None, description="Port of discharge.")
    cargo_cutoff: str | None = Field(
        default=None,
        description="Cargo cutoff datetime (ISO 8601).",
    )
    document_cutoff: str | None = Field(
        default=None,
        description="Document cutoff datetime (ISO 8601).",
    )
    containers_booked: int = Field(default=0, ge=0, description="Number of booked containers.")
    containers_confirmed: int = Field(
        default=0,
        ge=0,
        description="Number of confirmed containers.",
    )


# ---------------------------------------------------------------------------
# Support ticket
# ---------------------------------------------------------------------------


class SupportTicketRequest(MockApiBaseModel):
    """Input for the support ticket creation API."""

    customer_id: str = Field(..., description="Stable customer identifier.")
    subject: str = Field(..., description="Ticket subject line.")
    description: str = Field(..., description="Detailed issue description.")
    tenant_id: str = Field(..., description="Tenant routing identifier.")
    channel: str = Field(default="api", description="Ingress channel.")
    priority: str = Field(default="normal", description="Ticket priority level.")
    related_reference: str | None = Field(
        default=None,
        description="Optional reference (container number, booking number, etc.).",
    )
    request_id: str | None = Field(default=None, description="Optional correlation ID.")

    @field_validator("customer_id", "subject", "description", "tenant_id")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        """Reject blank required fields."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class SupportTicketData(MockApiBaseModel):
    """Response payload for the support ticket creation API."""

    ticket_id: str = Field(..., description="Stable ticket identifier.")
    status: str = Field(..., description="Current ticket status.")
    priority: str = Field(..., description="Ticket priority level.")
    subject: str = Field(..., description="Ticket subject line.")
    assigned_queue: str = Field(..., description="Assigned support queue.")
    estimated_response_hours: int = Field(
        ...,
        ge=0,
        description="Estimated response time in hours.",
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601).")
    customer_reference: str | None = Field(
        default=None,
        description="Customer-provided reference echoed from the request.",
    )
