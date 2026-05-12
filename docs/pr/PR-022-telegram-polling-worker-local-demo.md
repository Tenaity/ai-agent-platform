# PR-022: Telegram Polling Worker Local Demo

## Summary

Adds a local Telegram polling worker so a BotFather-created Telegram bot can
chat with the local AI Agent Runtime without public HTTPS deployment.

The worker uses Telegram `getUpdates` long polling, normalizes text updates into
Runtime API payloads, calls `/v1/agents/{agent_id}/invoke`, and sends the
Runtime API answer back with Telegram `sendMessage`.

## Scope

- Adds `apps/telegram-worker`
- Adds local worker settings, Telegram client, Runtime API client, normalizer,
  and polling loop
- Adds tests with fake Telegram and Runtime API clients
- Adds `make run-telegram-worker`
- Updates `.env.example`, README, and current chatbot demo docs
- Adds `docs/telegram-local-demo.md`

## Explicitly Not Added

- No Telegram webhook endpoint
- No public HTTPS deployment
- No route handler business logic
- No real production API calls
- No real LLM calls
- No database persistence
- No Grafana/Loki
- No real Telegram API calls in tests

## Architecture Notes

`apps/telegram-worker` is an integration/demo app. It does not add reusable
platform logic to apps and packages do not import it.

The worker calls the Runtime API HTTP boundary instead of importing
`InvocationService` directly. This keeps the local Telegram demo close to how a
deployed integration would invoke an agent while avoiding public webhook
requirements.

The bot token is read from `TELEGRAM_BOT_TOKEN` and is not included in startup
logs or test assertions.

## Tests

Added tests for:

- Telegram text update normalization to RuntimeRequest-compatible payload
- missing text and non-message updates ignored safely
- one text update processed through fake polling clients
- Runtime API client boundary called by polling orchestration
- RuntimeResponse answer sent back through Telegram client abstraction
- no real Telegram API calls in tests
- bot token not logged

## Risk

Low. The worker is local developer/demo tooling and is not wired into runtime
routes or production deployment. All tests use in-memory fakes.

## Follow-Up PRs

- Add a Telegram webhook facade for deployed demos.
- Add deployment skeleton for HTTPS webhook mode.
- Add structured local observability and Grafana/Loki demo wiring.
