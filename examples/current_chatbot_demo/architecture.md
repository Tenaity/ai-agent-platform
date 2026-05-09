# Current Chatbot Demo Architecture

```mermaid
flowchart TD
    Zalo["Zalo Webhook"] --> N8N["n8n Workflow"]
    N8N --> RuntimeAPI["Runtime API"]
    RuntimeAPI --> Agent["Customer Service Agent"]

    Agent --> Safety["Safety Pipeline"]
    Agent --> RAG["RAG Contracts"]
    RAG --> Qdrant["Future Qdrant Adapter"]
    Agent --> Tools["Tool Gateway + Audited Executor"]

    Tools --> Tracking["Mock Container Tracking API"]
    Tools --> Booking["Mock Booking Status API"]
    Tools --> Ticket["Mock Support Ticket API"]

    Agent --> RuntimeAPI
    RuntimeAPI --> N8N
    N8N --> Zalo
```

The boxes labeled future or mock describe intended integration points. This
example does not implement those services.

## Runtime Boundary

The Runtime API remains the only HTTP runtime entrypoint. Route handlers stay
thin and do not own retrieval, tool, or safety business logic.

## Retrieval Boundary

Future Qdrant retrieval should implement the `Retriever` interface and return
`RetrievalResult`. Answers should pass through `CitationEnforcer` when policy
requires citations.

## Tool Boundary

Production-like API calls should be modeled with `ToolSpec`, checked by
`ToolGateway`, executed through `PolicyAwareToolExecutor`, and audited through
`AuditAwareToolExecutor`.
