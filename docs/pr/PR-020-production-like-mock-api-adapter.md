# PR-020: Production-like Mock API Adapter

## Summary

Add deterministic customer-service mock API adapters so the current chatbot demo
can test tool workflows with production-like request/response schemas before
real company integrations exist.

## Scope

- Add typed mock API contracts under `agents/customer_service/mock_api`.
- Add `CustomerServiceMockApiClient` with deterministic local fixture data.
- Add `CustomerServiceMockApiToolExecutor` implementing `ToolExecutor` for the
  existing customer-service tool names.
- Keep and validate production-like schema examples under
  `examples/current_chatbot_demo/mock_api_schemas`.
- Add focused tests for schemas, mock client behavior, executor dispatch,
  invalid input, unknown tools, and no external HTTP requirements.
- Document mock API adapter boundaries.

## Explicitly Not Added

- No real TMS, CRM, Billing, support, or company API calls.
- No external HTTP calls.
- No real LLM calls.
- No RAG graph wiring.
- No route handler tool execution.
- No database persistence.
- No production auth.

## Architecture Notes

The adapter is agent-specific and lives under `agents/customer_service`. It
imports the domain-neutral `ToolExecutor` contracts from `packages`, but
packages must not import the agent or example code.

The mock executor is local-only and should be composed later with
`PolicyAwareToolExecutor` and `AuditAwareToolExecutor` before any graph wiring.

## Tests

- Mock API schemas validate through Pydantic models.
- Container tracking, booking status, and support ticket calls return
  deterministic production-like envelopes.
- The tool executor supports `tracking_container`, `check_booking_status`, and
  `create_support_ticket`.
- Invalid inputs and unknown tools return failed `ToolExecutionResult` objects.
- Tests assert no external HTTP clients are required.

## Risk

Low. This PR adds local deterministic test/demo adapters only and does not
change runtime route behavior or production integrations.

## Follow-up PRs

- Wire the current chatbot demo graph through the governed tool execution path.
- Add production API adapter skeletons behind the same contracts.
- Add n8n/Zalo facade endpoint wiring in a later PR.
