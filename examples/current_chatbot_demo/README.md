# Current Chatbot Demo

This example documents the reference customer-service chatbot project shape
that can be built on top of the platform. It is a reference implementation
plan, not production runtime code.

## Intended Flow

1. n8n receives a Zalo webhook payload.
2. n8n calls the Runtime API invoke endpoint.
3. The Runtime API selects the customer-service agent.
4. The agent may use future Qdrant retrieval through RAG contracts.
5. The agent may call production-like mocked APIs through Tool Gateway and
   audited tool execution.
6. n8n sends the response back to Zalo.

## Not Implemented In This PR

- No Qdrant adapter.
- No mock API server.
- No real Zalo or n8n facade endpoint.
- No production TMS, CRM, Billing, or support integrations.
- No real LLM calls.
- No persistence.

See `architecture.md`, `notes.md`, and the schema examples in this directory for
the intended future wiring.
