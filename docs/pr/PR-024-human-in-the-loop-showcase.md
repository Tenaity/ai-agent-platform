# PR-024: Human-in-the-loop Showcase

## Summary

Adds a local human-in-the-loop showcase for Telegram demo commands. High-risk
actions can be represented as pending approval requests and then approved or
rejected without database persistence, production integrations, or real LLM
calls.

## Scope

- Added reusable `snp_agent_core.human_loop` contracts.
- Added `ApprovalStore` and local `InMemoryApprovalStore`.
- Added Telegram `TelegramHumanLoopService` for `/human`, `/approve`,
  `/reject`, and `/approvals`.
- Updated polling flow so HITL commands return local Telegram responses without
  calling Runtime API.
- Added tests and documentation.

## Explicitly Not Added

- No database persistence.
- No production API calls.
- No real LLM calls.
- No webhook or deployment.
- No Grafana/Loki.
- No LangGraph interrupt/resume wiring yet.

## Architecture Notes

Human-in-the-loop concepts are reusable and live in `packages/snp_agent_core`.
The Telegram worker is only a demo UI that composes those contracts and store
interfaces. Packages do not import Telegram worker code.

Approval records store safe summaries and metadata. They should not contain raw
secrets or full sensitive payloads.

## Tests

- Approval contract validation.
- In-memory store create/get/list/approve/reject behavior.
- Unknown and already-decided approval errors.
- Telegram `/human`, `/approve`, `/reject`, and `/approvals` local behavior.
- Runtime API is not called for HITL local commands.
- Existing Telegram token redaction tests remain in place.

## Risk

The approval store is process-local and intentionally non-durable. Restarting
the worker clears pending approvals. This is acceptable for the local showcase
and should be replaced by a durable store in a future PR.

## Follow-up PRs

- Durable approval store using Postgres or Redis.
- LangGraph interrupt/resume integration.
- Runtime API visibility for pending approvals if needed.
- Operator UI beyond Telegram demo commands.
