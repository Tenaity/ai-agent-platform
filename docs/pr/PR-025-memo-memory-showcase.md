# PR-025: Memo / Memory Showcase

## Summary

Adds a local memo/memory showcase for Telegram. The demo can remember, recall,
list, and forget thread-scoped key/value memos without adding database
persistence, vector memory, real LLM calls, or production integrations.

## Scope

- Added reusable `snp_agent_memory` contracts.
- Added `MemoStore` and local `InMemoryMemoStore`.
- Added Telegram `TelegramMemoService` for `/memo remember`, `/memo get`,
  `/memo forget`, `/memo list`, and a simple booking memo question.
- Updated polling flow so memo commands return local Telegram responses without
  calling Runtime API.
- Added tests and documentation.

## Explicitly Not Added

- No database persistence.
- No Redis or Postgres.
- No vector memory.
- No long-term semantic memory.
- No real LLM calls.
- No production integrations.
- No webhook or deployment.
- No Grafana/Loki.

## Architecture Notes

Memo concepts are reusable and live in `packages/snp_agent_memory`. The
Telegram worker is only a demo UI that composes those contracts and store
interfaces. Packages do not import Telegram worker code.

`InMemoryMemoStore` is process-local and preserves insertion order. Repeated
`remember` calls for the same tenant/user/thread/key overwrite the value and
refresh `updated_at`.

## Tests

- Memo contract validation.
- In-memory store remember/get/list/overwrite/forget behavior.
- Unknown memo errors.
- Telegram `/memo` local command behavior.
- Runtime API is not called for memo local commands.
- Existing Telegram token redaction tests remain in place.
- `snp_agent_memory` does not import apps or Telegram worker code.

## Risk

The memo store is process-local and intentionally non-durable. Restarting the
worker clears memos. This is acceptable for the local showcase and should be
replaced by a durable or vector-backed store in a future PR when needed.

## Follow-up PRs

- Redis/Postgres-backed memo store.
- Vector-backed semantic memory.
- Memory policy and retention controls.
- Agent graph/runtime memory integration.
