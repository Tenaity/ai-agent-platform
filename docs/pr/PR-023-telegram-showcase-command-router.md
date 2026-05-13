# PR-023: Telegram Showcase Command Router

## Summary

Turns the local Telegram polling worker into a showcase cockpit for AI Agent
platform capabilities while keeping the worker thin. Telegram commands are
deterministic demo triggers: they either map to RuntimeRequest-compatible
payloads or return local placeholder responses for future capability PRs.

## Scope

- Add `telegram_worker.commands` for deterministic command parsing.
- Add `telegram_worker.showcase` for command-to-runtime/local-response mapping.
- Update polling to parse commands, send local responses, call Runtime API for
  runtime-backed commands, and store last metadata per chat for `/trace`.
- Add tests for command parsing, showcase mapping, trace metadata, free text,
  local responses, and token logging behavior.
- Update Telegram demo docs and current chatbot example docs.

## Explicitly Not Added

- No Grafana/Loki.
- No webhook.
- No deployment.
- No real production API calls.
- No real LLM calls.
- No database persistence.
- No route handler business logic.
- No real MCP, A2A, ACP, or DeepAgents implementation.

## Architecture Notes

The Telegram worker remains transport/demo UI only. It does not own RAG, tool,
human-loop, memory, MCP, A2A/ACP, or DeepAgents business logic. Runtime-backed
commands rewrite the message in a RuntimeRequest-compatible payload and call the
existing Runtime API boundary. Capability behavior remains in agents or reusable
packages.

Placeholder commands document the planned roadmap without faking production
capabilities:

- `/human` -> PR-024
- `/memo` -> PR-025
- `/skill` -> PR-026
- `/mcp` -> PR-027
- `/a2a` and `/acp` -> PR-028
- `/eval` -> PR-029/PR-031
- `/deepagent` -> PR-030

## Tests

Added coverage for:

- command parser for `/help`, `/rag`, `/tool container`, `/booking`, `/ticket`
- free text bypassing command mode
- `/help` and `/showcase` local responses
- placeholder command local responses
- `/rag`, `/tool container`, `/booking`, and `/ticket` RuntimeRequest mapping
- `/trace` using last metadata
- free text still invoking Runtime API
- Telegram bot token not logged

## Risk

Low. The router is deterministic and local to `apps/telegram-worker`. It does
not change Runtime API routes, agent graph behavior, package contracts, or
external integrations.
