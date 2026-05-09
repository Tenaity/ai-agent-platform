# Current Chatbot Demo Reference Project

This example shows how the platform scaffold can be applied to the user's
current customer-service chatbot demo. It is a reference project shape, not
production runtime code.

The demo is intentionally kept under `examples/` because this repository is an
AI Agent Platform scaffold, not a single chatbot implementation.

## Intended Flow

1. Zalo sends a webhook event to an n8n workflow.
2. n8n normalizes the event into a platform `RuntimeRequest`.
3. n8n calls the Runtime API invoke endpoint.
4. The Runtime API invokes the customer-service agent graph.
5. The graph performs safety precheck, intent routing, RAG/tool branch
   selection, and answer formatting.
6. Future Qdrant retrieval returns `RetrievalResult` objects with citations.
7. Future mock API adapters execute production-like internal API calls through
   Tool Gateway, execution, and audit boundaries.
8. n8n formats the `RuntimeResponse` back to Zalo.

## Structure

- `agent/`: reference customer-service agent project shape for this demo.
- `qdrant/`: future Qdrant adapter config and payload schema examples.
- `mock_api_schemas/`: production-like request/response envelopes for mock
  internal APIs.
- `n8n/`: Zalo webhook input and Runtime API request examples.
- `architecture.md`: boundary diagram and intended graph flow.
- `notes.md`: follow-up PR notes and non-goals.

## Not Implemented

- No real Qdrant adapter or Qdrant connection.
- No real production API calls.
- No real LLM calls.
- No runtime route changes.
- No database persistence.
- No Docker deployment.

Follow-up PRs can add the Qdrant retriever adapter, production-like mock API
adapters, and n8n/Zalo facade endpoint while keeping platform packages reusable
and route handlers thin.

