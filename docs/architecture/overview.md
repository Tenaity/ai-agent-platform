# Architecture Overview

The SNP AI Agent Platform is organized as layered, reusable runtime
infrastructure for domain-specific agents.

## Layers

- Runtime API: thin HTTP facade for health, version, invocation, and future
  administrative operations.
- Agent Registry: loads and validates `agent.yaml` manifests before agents are
  exposed to runtime processes.
- LangGraph Runtime: future graph execution adapter responsible for stateful
  workflow orchestration.
- Tool Gateway: the only approved path for tool execution, policy checks, audit
  metadata, and fake-tool testing.
- Memory: scoped storage contracts for session, user, and domain memory.
- RAG: retrieval contracts, indexing boundaries, and citation expectations.
- Safety: guardrails, policy enforcement, review routing, and refusal behavior.
- Observability: tracing, structured events, run metadata, and future LangSmith
  integration.
- Eval: regression datasets, scenario runners, acceptance thresholds, and
  release gates.

Apps should expose these capabilities without owning domain-neutral logic.
Packages should own reusable contracts and runtime behavior. Agents should own
domain-specific behavior declarations and tests.
