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
- PR-003: expose a thin Runtime API shell around core contracts.
- PR-004: introduce a minimal LangGraph-backed hello runtime.
- PR-005: add a LangSmith tracing skeleton for graph executions.
- PR-006: add local-first regression evaluation skeleton with deterministic evaluators.
- PR-007: introduce runtime execution lifecycle — request IDs, run IDs, InvocationService, and AgentRun contracts.

LangChain, LangGraph, and LangSmith dependencies are intentionally deferred
until the runtime contracts are ready to absorb them cleanly.

## Development

```bash
make install
make lint
make typecheck
make test
```

Run the regression eval for an agent:

```bash
make eval AGENT=snp.customer_service.zalo DATASET=datasets/customer_service/regression_v1.jsonl
```

Run the runtime API locally:

```bash
make run-runtime-api
```

Then visit `GET /health` or `GET /version`.

Runtime API examples:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/version
curl http://localhost:8000/v1/agents
curl http://localhost:8000/v1/agents/customer_service/manifest
curl -X POST http://localhost:8000/v1/agents/customer_service/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_demo",
    "channel": "api",
    "user_id": "user_123",
    "thread_id": "thread_456",
    "message": "How do I reset my password?",
    "metadata": {"locale": "en-US"}
  }'
```

## Architectural Guardrails

- Apps stay thin and delegate reusable behavior to packages.
- Public boundaries use typed contracts, usually Pydantic models.
- Agent behavior must be versioned, testable, and evaluable.
- Tool execution must eventually flow through a Tool Gateway.
- API route handlers must not call LLMs directly.
- Secrets belong in environment variables, never source control.
