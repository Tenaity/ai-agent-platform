# SNP AI Agent Platform

`snp-ai-agent-platform` is an internal SDK and runtime foundation for building
modular, traceable, evaluable, memory-aware, tool-governed, safety-bounded, and
reusable AI agent workflows.

This repository is a platform/framework. It is not a one-off chatbot, a demo
prompt collection, or a place for product-specific business logic to leak into
runtime apps.

## Repository Layout

- `apps/`: thin API, CLI, and worker entrypoints.
- `packages/`: reusable, domain-neutral platform primitives.
- `agents/`: versioned, domain-specific agent definitions.
- `prompts/`: shared and agent-specific prompt assets.
- `datasets/`: evaluation datasets and documentation.
- `docs/`: architecture, ADRs, and operating playbooks.
- `infra/`: future deployment infrastructure placeholders.

## PR Roadmap

- PR-001: establish the monorepo scaffold, contracts, docs, and tests.
- PR-002: add agent registry loading and manifest discovery.
- PR-003: introduce LangGraph runtime abstractions behind typed interfaces.
- PR-004: add Tool Gateway contracts with fake-tool integration tests.
- PR-005: add memory, RAG, safety, observability, and evaluation integrations.

LangChain, LangGraph, and LangSmith dependencies are intentionally deferred
until the runtime contracts are ready to absorb them cleanly.

## Development

```bash
make install
make lint
make typecheck
make test
```

Run the runtime API locally:

```bash
make run-runtime-api
```

Then visit `GET /health` or `GET /version`.

## Architectural Guardrails

- Apps stay thin and delegate reusable behavior to packages.
- Public boundaries use typed contracts, usually Pydantic models.
- Agent behavior must be versioned, testable, and evaluable.
- Tool execution must eventually flow through a Tool Gateway.
- API route handlers must not call LLMs directly.
- Secrets belong in environment variables, never source control.
