# Notes

This example is intentionally documentation, schemas, and placeholder agent
shape only. No real integrations are wired here.

## What This PR Does (PR-018)

PR-018 establishes the reference project structure for the current chatbot demo
under `examples/current_chatbot_demo`. It documents the intended graph shape,
data flow, and schema contracts without implementing production integrations.

This PR wires:
- Reference agent project structure (agent.yaml, graph.py, state.py, prompts,
  evals)
- Qdrant config and payload schema examples
- Production-like mock API request/response envelopes
- n8n/Zalo webhook and Runtime API payload examples
- Architecture boundary documentation

## Future Wiring

| PR | Scope |
|---|---|
| PR-019 | Qdrant Retriever Adapter — implement `Retriever` interface backed by Qdrant |
| PR-020 | Production-like Mock API Adapter — implement `ToolExecutor` with audited mock responses |
| PR-021 | n8n/Zalo Facade Endpoint — thin HTTP route for Zalo webhook normalization |

## Boundaries (Non-Negotiable)

- `examples/` are reference projects, not framework packages.
- Packages must **not** import this example.
- Retrieval must return platform `RetrievalResult` objects.
- Answers that rely on retrieval must use citation enforcement.
- Tool calls must flow through Tool Gateway policy and audit wrappers.
- Secrets belong in environment variables and must not appear in example files.
- No real Qdrant connection credentials, real API keys, or real webhook tokens.

## State Schema Evolution

The `CurrentChatbotDemoState` TypedDict is intentionally permissive (total=False)
to allow graph nodes to add fields incrementally as the demo evolves. When this
agent is promoted to a production agent under `agents/`, the state schema should
be frozen and validated at graph boundaries.

## Eval Notes

`agent/evals/eval.yaml` defines regression eval cases for the reference graph
step routing only. It does not run real LLM assertions or real retrieval. A
future production dataset should live under `datasets/customer_service/`.

## Known Limitations

- `graph.py` returns a simple tuple of step names, not a real LangGraph
  `StateGraph`. This is intentional — it documents intent without requiring
  LangGraph execution environment configuration.
- `agent.yaml` references `examples.current_chatbot_demo.agent.graph:build_graph`
  which will resolve correctly once the `examples/` directory is on `sys.path`,
  but this agent is not registered with the Runtime API in this PR.
