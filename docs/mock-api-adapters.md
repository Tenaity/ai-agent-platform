# Production-Like Mock API Adapters

PR-020 adds deterministic customer-service mock API adapters for the current
chatbot demo. They mimic production request/response shapes without calling
real TMS, CRM, billing, support, or company systems.

## Purpose

The mock adapters let tool workflows be tested against realistic API envelopes
before real integrations exist. They are local-only and side-effect-free:

- no HTTP clients
- no production credentials
- no database persistence
- no real internal systems
- no LLM calls
- no runtime route wiring

## Location

The reference schema examples live under:

```text
examples/current_chatbot_demo/mock_api_schemas/
```

The executable mock adapter lives under:

```text
agents/customer_service/mock_api/
```

This is agent-specific code. Packages must not import it.

## Response Envelope

All mock API responses follow a production-like envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "mock-request-id"
}
```

The envelope is modeled by `ApiEnvelope[T]` with `ApiError` for failed
responses. The mock client currently returns successful deterministic envelopes,
including `not_found` status data for unknown records.

## Supported APIs

The mock client supports:

- `track_container(ContainerTrackingRequest)`
- `get_booking_status(BookingStatusRequest)`
- `create_support_ticket(SupportTicketRequest)`

Fixtures are static and deterministic so tests can assert exact outputs.

## Tool Executor Adapter

`CustomerServiceMockApiToolExecutor` implements the platform `ToolExecutor`
interface for these customer-service tool names:

- `tracking_container`
- `check_booking_status`
- `create_support_ticket`

It converts `ToolExecutionRequest.input` into typed Pydantic request models,
calls the local mock client, and returns `ToolExecutionResult`. Invalid input or
unknown tool names return safe failed results.

PR-021 wires the executor into the customer-service demo graph behind
`PolicyAwareToolExecutor`, `ToolGateway`, and `AuditAwareToolExecutor`. It is
still not wired into runtime routes and still does not call any external
company systems.

## Future Real Adapters

Real adapters can later implement the same request/response shape and executor
boundary while adding production concerns such as authentication, retries,
timeouts, rate limits, and observability. Those real adapters must not be added
inside route handlers.
