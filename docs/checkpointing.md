# LangGraph Checkpointing

PR-008 introduced a small checkpoint abstraction for LangGraph execution state.
It gives the runtime a stable place to attach future human-in-the-loop, resume,
durable workflow, and memory-adjacent features without coupling route handlers
to LangGraph implementation details.

## What Checkpointing Is

Checkpointing stores graph execution state between LangGraph steps and turns.
When enabled, the runtime compiles the graph with a LangGraph checkpointer and
passes the request `thread_id` into the graph execution config:

```json
{
  "configurable": {
    "thread_id": "thread_456"
  }
}
```

`thread_id` is the continuity key. The caller owns it, and every request that
belongs to the same conversation should use the same value.

## What Checkpointing Is Not

Checkpointing is not long-term semantic memory. It does not decide what facts
to remember about a user, does not run retrieval, and does not replace a future
Memory Manager. It only persists or retains LangGraph execution state in the
backend selected by runtime configuration.

## Configuration

Runtime processes configure checkpointing with environment variables:

| Variable | Default | Description |
|---|---|---|
| `SNP_CHECKPOINT_BACKEND` | `none` | Checkpoint backend. Supported values: `none`, `memory`. |
| `SNP_CHECKPOINT_NAMESPACE` | unset | Optional LangGraph checkpoint namespace. |

Supported backends:

- `none`: no checkpointer; current stateless execution behavior.
- `memory`: in-process LangGraph checkpointer for local development and tests.

The abstraction lives in `snp_agent_core.checkpointing`:

- `CheckpointBackend`
- `CheckpointConfig`
- `build_checkpointer(config)`

Apps configure runtime behavior and pass the resulting checkpointer into core
graph loading. Packages do not import from apps.

## Persistence Roadmap

There is no database persistence in PR-008. Postgres-backed checkpointing will
come later behind the same factory boundary, after persistence contracts and
operational requirements are defined. This PR deliberately does not add RAG,
tools, memory management, safety, real LLM calls, or database dependencies.

See [architecture/runtime-flow.md](architecture/runtime-flow.md) for where the
checkpoint factory sits in the runtime path.
