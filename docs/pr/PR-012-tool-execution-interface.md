# PR-012 Tool Execution Interface

## Summary

- Add domain-neutral tool execution request/result contracts.
- Add `ToolExecutor` as the abstract interface for future tool adapters.
- Add `PolicyAwareToolExecutor` to compose `ToolGateway` policy checks with a
  wrapped executor.
- Add test-only fake executor utilities and regression tests for denied,
  approval-required, delegated, failed, and latency-preserving execution paths.
- Document the execution boundary and future adapter path.

## Scope

- `packages/snp_agent_tools`
- `packages/snp_agent_tools/tests`
- `tests`
- `docs`
- `docs/pr`

## Explicitly Not Added

- Real TMS, CRM, Billing, support, or third-party integrations
- Real external API calls
- RAG
- Memory Manager
- Safety pipeline
- Real LLM calls
- Database persistence
- Tool execution inside route handlers

## Architecture Notes

- `ToolGateway` decides permission.
- `ToolExecutor` executes a capability after policy permits it.
- `PolicyAwareToolExecutor` checks policy first and delegates only when allowed.
- Executor exceptions are mapped to safe failed results without stack traces.
- Real adapters will come later behind the `ToolExecutor` interface.

## Tests

- Valid `ToolExecutionRequest`
- Valid `ToolExecutionResult`
- Denied policy returns denied result
- Requires-approval policy returns requires-approval result
- Allowed policy delegates to executor
- Executor exception returns failed result
- Failed result does not leak stack trace
- Executor latency is preserved

## Risk

- Low. This PR adds contracts, an abstract interface, a deterministic wrapper,
  and tests only.
- No external calls, credentials, route wiring, or persistence are added.

## Follow-up PRs

- Add fake-tool execution adapters.
- Add safety skeleton.
- Add RAG contracts.
- Add audit events around policy and execution decisions.
- Add real integrations only after fake-tool behavior and policy boundaries are
  stable.
