# Telegram Local Demo

PR-022 adds a local Telegram polling worker so a BotFather-created bot can chat
with the local Runtime API without public HTTPS deployment. PR-023 turns that
worker into a lightweight showcase cockpit for platform capabilities. PR-024
adds local human-in-the-loop approval commands. PR-025 adds local thread-scoped
memo commands. PR-026 adds local metadata-driven skill commands.

## Why Polling

Telegram supports two bot update modes:

- `getUpdates` long polling: the local worker asks Telegram for new messages.
- webhook: Telegram pushes messages to a public HTTPS endpoint.

This PR uses long polling only. It does not add a webhook endpoint, public
deployment, database persistence, real LLM calls, or real production API calls.

## Setup

1. Open Telegram and create a bot with BotFather.
2. Put the token in `.env`:

```bash
TELEGRAM_BOT_TOKEN=123456:replace-with-your-token
TELEGRAM_AGENT_ID=customer_service
TELEGRAM_TENANT_ID=demo
RUNTIME_API_BASE_URL=http://localhost:8000
TELEGRAM_POLL_TIMEOUT_SECONDS=30
```

Do not commit the real token. `.env.example` documents the variable names only.

## Run Locally

Start the Runtime API:

```bash
make run-runtime-api
```

Before starting the worker, verify the agent id exposed by the local Runtime
API:

```bash
curl http://localhost:8000/v1/agents
```

Set `TELEGRAM_AGENT_ID` to one of the returned agent ids. The default for the
current demo is `customer_service`.

In another terminal, start the Telegram worker:

```bash
make run-telegram-worker
```

Then chat with the bot in Telegram. The worker normalizes text updates into
`RuntimeRequest` payloads and posts them to:

```text
POST /v1/agents/{agent_id}/invoke
```

The worker sends the Runtime API answer back through Telegram `sendMessage`.

## Showcase Commands

Telegram is the local AI Agent showcase cockpit. Commands are deterministic demo
triggers that either rewrite the user text into a RuntimeRequest-compatible
message or return a local placeholder response for a future platform capability.

Supported commands:

- `/help`
- `/showcase`
- `/rag <question>`
- `/tool container <container_no>`
- `/booking <booking_no>`
- `/ticket <message>`
- `/trace`
- `/human <message>`
- `/approve <approval_id>`
- `/reject <approval_id>`
- `/approvals`
- `/memo remember <key> <value>`
- `/memo get <key>`
- `/memo forget <key>`
- `/memo list`
- `/skill list`
- `/skill show <skill_id>`
- `/skill run <skill_id>`
- `/mcp <command>`
- `/a2a <message>`
- `/acp <message>`
- `/deepagent <task>`
- `/eval`

Recommended demo script:

```text
1. /rag giờ làm việc
2. /tool container ABCD1234567
3. /booking BK123
4. /ticket Tôi cần hỗ trợ
5. /trace
6. /human yêu cầu hoàn phí lưu bãi
7. /memo remember booking BK123
8. /memo what is my booking?
9. /skill list
10. /skill show container_tracking_triage
11. /skill run support_ticket_creation
12. /mcp list
13. /a2a ask billing_agent giải thích phí
14. /deepagent lập kế hoạch xử lý khiếu nại
```

Some commands are placeholders for future PRs. The worker remains thin: it does
not own RAG, tool, memory, MCP, A2A/ACP, or DeepAgents business logic.
Capability logic belongs in agents or reusable packages.

Human-in-the-loop commands are local demo commands backed by the reusable
`snp_agent_core.human_loop` contracts and `InMemoryApprovalStore`. They do not
execute real production actions, persist to a database, or call Runtime API in
PR-024.

Memo commands are local demo commands backed by the reusable `snp_agent_memory`
contracts and `InMemoryMemoStore`. They are thread-scoped key/value memos for
the current Telegram worker process. They are not long-term semantic memory,
vector memory, or database-backed memory.

Skill commands are local demo commands backed by `snp_agent_core.skills`.
Skills are reusable workflow capability templates loaded from YAML metadata.
The demo can list, show, and simulate a skill run, but it does not execute
arbitrary code, call an LLM, call tools, or call external APIs.

## Boundary

The worker is an integration/demo app under `apps/telegram-worker`. It calls the
Runtime API HTTP boundary and does not import `InvocationService` directly.
Tests inject fake Telegram and Runtime API clients, so no real Telegram API call
or external service call is required in CI.

## Future Work

Future PRs can add durable approval persistence, LangGraph interrupt/resume,
Redis/Postgres/vector-backed memory, skill graph wiring, MCP, agent interop,
DeepAgents, webhook mode, deployment, richer observability, and Grafana/Loki.
Those should stay separate from this local polling demo.
