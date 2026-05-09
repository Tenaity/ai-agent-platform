# PR-017: Agent Project Generator CLI Skeleton

## Summary

Add a local developer CLI skeleton that generates new agent projects from the
PR-016 templates.

## Scope

- Add `apps/agent-cli` with a small stdlib-only CLI.
- Support `create-agent` with `--template`, `--name`, `--domain`,
  `--output-dir`, and `--dry-run`.
- Render template placeholders through deterministic string replacement.
- Add generator unit tests.
- Update README and scaffold/development docs.

## Explicitly Not Added

- No real Qdrant integration.
- No real production API integration.
- No real LLM calls.
- No runtime behavior changes.
- No database persistence.
- No route handler logic.
- No automatic agent registration or deployment.

## Architecture Notes

The CLI is local developer tooling under `apps/`. It generates scaffold files
from `templates/` into an agent project directory, but generated projects still
need human review, tests, evals, and normal runtime registration decisions.

Templates remain scaffolds, not runtime code. Packages remain reusable and
domain-neutral.

## Tests

- `apps/agent-cli/tests/test_generator.py` covers basic generation, RAG
  generation, dry-run behavior, unknown templates, existing target directories,
  placeholder replacement, and required generated files.

## Risk

Low. The change is additive developer tooling and does not alter Runtime API
behavior or existing agent execution.

## Follow-up PRs

- PR-018 Current Chatbot Demo Reference Project Wiring
- PR-019 Qdrant Retriever Adapter
- PR-020 Production-like Mock API Adapter
- PR-021 n8n/Zalo Facade Endpoint

