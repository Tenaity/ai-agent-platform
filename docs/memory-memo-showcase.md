# Memo / Memory Showcase

PR-025 adds a local memo showcase for Telegram so the demo can show
thread-scoped memory without database persistence or long-term semantic memory.

This is small explicit memory: a user tells the bot to remember a key/value
pair, then recalls or deletes it later in the same Telegram thread.

## Contracts

`snp_agent_memory` defines:

- `MemoScope`: `thread`, `user`, or `tenant`
- `MemoRecord`: a Pydantic memo record with key, value, scope, tenant, user,
  optional thread, UTC timestamps, and safe metadata
- `MemoStore`: persistence boundary for remember/get/forget/list operations
- `InMemoryMemoStore`: local/demo store backed by process memory

Memo records are domain-neutral and should not store secrets.

## Telegram Commands

The Telegram worker is only the demo UI. It composes the reusable memory store
through `TelegramMemoService`.

```text
/memo remember <key> <value>
/memo get <key>
/memo forget <key>
/memo list
/memo what is my booking?
```

Examples:

```text
/memo remember booking BK123
/memo get booking
/memo what is my booking?
/memo forget booking
```

All memo commands return local Telegram responses and do not call Runtime API in
PR-025.

## Non-Goals

- No database persistence
- No Redis or Postgres
- No vector memory
- No semantic memory
- No real LLM calls
- No production integrations
- No webhook or deployment

Future PRs can add durable Redis/Postgres stores, vector-backed memory, memory
policy, retention controls, and graph/runtime integration.
