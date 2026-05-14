# PR-026: Skills Showcase

## Summary

Adds a reusable metadata-driven skills showcase. Telegram can list, inspect,
and simulate running workflow capability templates without real LLM calls,
production integrations, or deployment.

## Scope

- Added `snp_agent_core.skills` contracts, registry, and YAML loader.
- Added sample skill metadata under `skills/`.
- Added Telegram `TelegramSkillsService` for `/skill list`, `/skill show`, and
  `/skill run`.
- Updated polling so skill commands return local Telegram responses without
  calling Runtime API.
- Added tests and documentation.

## Explicitly Not Added

- No real LLM calls.
- No real production API calls.
- No MCP/A2A/ACP implementation.
- No database persistence.
- No webhook or deployment.
- No Grafana/Loki.
- No arbitrary code execution from skills.

## Architecture Notes

Skill concepts are reusable and live in `packages/snp_agent_core`. Skill files
are metadata-only YAML documents loaded from `skills/*/skill.yaml`. The loader
validates metadata with Pydantic and does not execute code.

The Telegram worker remains a demo UI that composes the registry and formats
responses. Packages do not import Telegram worker code.

## Tests

- Skill contract validation.
- Duplicate skill rejection.
- Unknown skill rejection.
- YAML loader loads sample skills.
- Telegram `/skill list`, `/skill show`, and `/skill run` local behavior.
- Runtime API is not called for skill local commands.
- Existing Telegram token redaction tests remain in place.
- Core skills package does not import apps or Telegram worker code.

## Risk

The simulated runner is intentionally not a real executor. It demonstrates
workflow shape only. Future graph execution must still pass through existing
runtime, safety, tool, and audit boundaries.

## Follow-up PRs

- Wire selected skills into LangGraph agent workflows.
- Add skill policy and authorization.
- Add richer skill discovery and filtering.
- Add tests for graph-level skill execution once execution exists.
