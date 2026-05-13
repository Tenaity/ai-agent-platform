# Telegram Local Demo

PR-022 adds a local Telegram polling worker so a BotFather-created bot can chat
with the local Runtime API without public HTTPS deployment. PR-023 turns that
worker into a lightweight showcase cockpit for platform capabilities. PR-024
adds local human-in-the-loop approval commands.

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
- `/memo <message>`
- `/skill <command>`
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
8. /mcp list
9. /a2a ask billing_agent giải thích phí
10. /deepagent lập kế hoạch xử lý khiếu nại
```

Some commands are placeholders for future PRs. The worker remains thin: it does
not own RAG, tool, memory, MCP, A2A/ACP, or DeepAgents business logic.
Capability logic belongs in agents or reusable packages.

Human-in-the-loop commands are local demo commands backed by the reusable
`snp_agent_core.human_loop` contracts and `InMemoryApprovalStore`. They do not
execute real production actions, persist to a database, or call Runtime API in
PR-024.

## Boundary

The worker is an integration/demo app under `apps/telegram-worker`. It calls the
Runtime API HTTP boundary and does not import `InvocationService` directly.
Tests inject fake Telegram and Runtime API clients, so no real Telegram API call
or external service call is required in CI.

## Future Work

Future PRs can add durable approval persistence, LangGraph interrupt/resume,
memory/memo, skills, MCP, agent interop, DeepAgents, webhook mode, deployment,
richer observability, and Grafana/Loki. Those should stay separate from this
local polling demo.
