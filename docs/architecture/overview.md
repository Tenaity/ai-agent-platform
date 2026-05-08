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

## Core Runtime Contracts

PR-002 establishes the serialized contract layer before any real agent
execution exists. `snp_agent_core.contracts` defines the Pydantic models that
future runtime adapters will consume and produce:

- `AgentManifest` validates versioned agent declarations from `agent.yaml`.
- `RuntimeRequest` is the inbound message and routing envelope accepted by the
  platform runtime.
- `RuntimeContext` is the normalized execution context shared between runtime
  components.
- `RuntimeResponse` is the outbound result envelope with run status, answer,
  citations, tool call records, trace linkage, handoff state, and metadata.
- `Citation`, `ToolCallRecord`, and `AgentRunStatus` keep provenance, tool
  auditing, and run state serializable without binding core packages to a graph
  engine or provider SDK.

These contracts are boundaries, not execution code. LangGraph, LangChain, and
LangSmith integrations should be introduced behind these models in later PRs.

## Runtime API Responsibilities

PR-003 adds a production-shaped Runtime API shell around the core contracts. The
API is responsible for HTTP routing, request/response validation, manifest
discovery through the file-backed registry, and structured API errors.

The Runtime API is not responsible for graph execution, direct LLM calls, or
direct tool calls. `POST /v1/agents/{agent_id}/invoke` validates the agent and
request body, then returns a scaffold `RuntimeResponse` until a later PR adds a
runtime adapter behind the same contract.

## LangGraph Runtime

PR-004 introduces the first minimal LangGraph-backed execution path. Agent
manifests declare a runtime type, graph builder import path, and state schema
import path. The Runtime API loads the manifest, delegates graph loading to
`snp_agent_core.graph`, and returns the graph result as a `RuntimeResponse`.

The current customer service graph is deterministic and does not call LLMs,
tools, external APIs, persistence, or LangSmith. The graph runner is the
extension point where later PRs can add checkpointers, tracing, tool mediation,
memory, RAG, and safety enforcement behind the same API contract.

## Checkpointing

PR-008 adds a checkpoint abstraction for LangGraph execution state. Runtime
processes select a backend with `SNP_CHECKPOINT_BACKEND`; the default `none`
backend preserves stateless execution, while `memory` enables an in-process
LangGraph checkpointer for local development and tests.

Checkpointing is graph execution state, not long-term semantic memory. It does
not add RAG, tools, a Memory Manager, safety, real LLM calls, or database
persistence. When enabled, the graph runner passes `thread_id` into LangGraph
execution config so the caller-owned conversation key becomes the continuity
key for future resume, human-in-the-loop, and durable workflow features.

Postgres checkpointing will come later behind
`snp_agent_core.checkpointing.build_checkpointer()` after persistence contracts
are introduced.

## Observability

PR-005 adds a LangSmith tracing skeleton without dashboards or evals. The
Runtime API builds a `RuntimeContext`, derives standard trace metadata from the
context and `AgentManifest`, and passes that metadata into graph execution
config. Tracing remains disabled by default and local tests do not require
LangSmith credentials.

## Runtime Execution Lifecycle

PR-007 introduces a clean invocation lifecycle before tools, memory, RAG,
safety, or real LLM integrations are added.

**Three runtime identifiers** — each with a distinct scope and owner:

| Identifier | Owner | Scope | Purpose |
|---|---|---|---|
| `thread_id` | caller | conversation (many turns) | context continuity, future memory key |
| `request_id` | middleware or caller | one HTTP request | HTTP-level correlation |
| `run_id` | platform (`InvocationService`) | one graph execution | execution audit, future persistence key |

**`RequestIdMiddleware`** reads `X-Request-ID` from the inbound request or
generates a UUID4. The ID is written to `request.state.request_id` and echoed
back in the `X-Request-ID` response header for caller correlation.

**`InvocationService`** extracts all execution orchestration from the route
handler: manifest loading, `run_id` generation, `RuntimeContext` construction,
wall-clock timing, trace metadata, and error mapping. Route handlers read the
request ID from middleware state and delegate everything else to the service.

**`AgentRun`** (in `snp_agent_core.contracts.runs`) is the typed lifecycle
record for one invocation. It is constructed but not yet persisted. The
`run_id`, `request_id`, and `duration_ms` surface in
`RuntimeResponse.metadata`. Future PRs will persist the full `AgentRun` record.

Every `RuntimeResponse` from a successful invocation now contains:

```json
{
  "metadata": {
    "run_id": "<uuid>",
    "request_id": "<uuid-or-caller-supplied>",
    "duration_ms": 12
  }
}
```

See [runtime-lifecycle.md](../runtime-lifecycle.md) for the full invocation
flow, identifier semantics, and where future integrations attach.
See [checkpointing.md](../checkpointing.md) for checkpoint configuration and
semantics.
