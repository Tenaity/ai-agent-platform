# Telegram Local Demo

PR-022 adds a local Telegram polling worker so a BotFather-created bot can chat
with the local Runtime API without public HTTPS deployment.

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

## Boundary

The worker is an integration/demo app under `apps/telegram-worker`. It calls the
Runtime API HTTP boundary and does not import `InvocationService` directly.
Tests inject fake Telegram and Runtime API clients, so no real Telegram API call
or external service call is required in CI.

## Future Work

Future PRs can add webhook mode, deployment, richer observability, and
Grafana/Loki. Those should stay separate from this local polling demo.
