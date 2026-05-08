# Runtime Flow

The runtime path keeps HTTP concerns in `apps/runtime-api` and reusable
execution behavior in packages. Route handlers stay thin; `InvocationService`
owns manifest lookup, lifecycle IDs, trace metadata, checkpoint configuration,
graph loading, timing, and clean failure responses.

```mermaid
flowchart TD
    Client["External Client"] --> API["Runtime API"]
    API --> RequestId["RequestIdMiddleware"]
    RequestId --> Route["invoke_agent route"]
    Route --> Service["InvocationService"]
    Service --> Registry["FileAgentRegistry"]
    Registry --> Manifest["AgentManifest"]
    Service --> Trace["build_trace_metadata"]
    Service --> Checkpoint["build_checkpointer"]
    Service --> Loader["load_graph_runner"]
    Loader --> Graph["Compiled LangGraph"]
    Graph --> Runner["GraphRunner"]
    Runner --> Response["RuntimeResponse"]
    Service --> Metadata["run_id / request_id / duration_ms"]
    Metadata --> API
    API --> Client
```

## Implemented Today

- `GET /health`
- `GET /version`
- `GET /v1/agents`
- `GET /v1/agents/{agent_id}/manifest`
- `POST /v1/agents/{agent_id}/invoke`
- Deterministic customer service LangGraph hello workflow
- Clean failed `RuntimeResponse` for unexpected graph exceptions

## Future

- Real model providers
- Streaming
- persisted `AgentRun` records
- durable checkpoint backends
- execution-capable Tool Gateway adapters
