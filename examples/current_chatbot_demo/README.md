# Current Chatbot Demo Reference Project

This directory is a **reference project** that documents how the SNP AI Agent
Platform scaffold applies to the user's current customer-service chatbot demo.
It is project structure, schemas, and documentation only — not production
runtime code.

The demo lives under `examples/` because this repository is a platform
framework, not a single chatbot implementation. Real production logic belongs in
`agents/` (versioned, testable, evaluable) once the wiring is validated here.

---

## Intended End-to-End Flow

```
Zalo (user sends message)
  → n8n workflow receives Zalo webhook event
  → n8n normalizes event into a platform RuntimeRequest
  → n8n calls Runtime API: POST /v1/agents/{agent_id}/invoke
  → Runtime API applies RequestIdMiddleware + InvocationService
  → InvocationService loads agent manifest + runs safety precheck
  → Agent graph executes:
      Safety precheck node
      → Intent routing node
      → RAG branch (future Qdrant retriever adapter)
          → RetrievalResult + CitationEnforcer
      → Tool branch (production-like mock API adapters)
          → ToolGateway policy check → executor → audit record
      → Answer formatting node
  → RuntimeResponse returned to n8n
  → n8n formats reply and sends back to Zalo user
```

See `architecture.md` for the full boundary diagram and node-level description.

---

## Directory Structure

```
examples/current_chatbot_demo/
├── README.md                         ← this file
├── architecture.md                   ← boundary diagram and graph shape
├── notes.md                          ← follow-up PR notes and non-goals
├── agent/
│   ├── README.md                     ← agent sub-project description
│   ├── agent.yaml                    ← reference agent manifest
│   ├── graph.py                      ← placeholder graph shape
│   ├── state.py                      ← typed state sketch
│   ├── prompts/
│   │   ├── system.md                 ← system prompt placeholder
│   │   └── rag_answer.md             ← RAG answer formatting prompt
│   └── evals/
│       └── eval.yaml                 ← reference eval case definitions
├── qdrant/
│   ├── config.example.yaml           ← Qdrant retriever config shape
│   └── payload_schema.example.json   ← example document payload fields
├── mock_api_schemas/
│   ├── container_tracking.request.example.json
│   ├── container_tracking.response.example.json
│   ├── booking_status.request.example.json
│   ├── booking_status.response.example.json
│   ├── support_ticket.request.example.json
│   └── support_ticket.response.example.json
└── n8n/
    ├── zalo_webhook_payload.example.json    ← raw Zalo OA webhook event
    └── runtime_api_request.example.json     ← normalized RuntimeRequest from n8n
```

---

## Agent Graph Shape (Reference)

The reference agent documents this intended future graph:

```
Input
→ Safety precheck         (SafetyPipeline: rule-based + optional PII redaction)
→ Intent routing          (classify: rag / tool / direct_answer)
→ RAG branch              (future Qdrant retriever → RetrievalResult + citations)
→ Tool branch             (mock API adapters → ToolGateway → audit)
→ Answer formatting       (CitationEnforcer when citations required)
→ RuntimeResponse
```

Placeholder code in `agent/graph.py` documents the step names without
implementing real retrieval, tool execution, or LLM calls.

---

## Qdrant Retrieval (Future)

`qdrant/config.example.yaml` shows the retriever config fields needed by a
future Qdrant adapter implementing the platform `Retriever` interface.

`qdrant/payload_schema.example.json` shows the document payload shape expected
in the Qdrant collection (text, title, uri, source_id, doc_type, department,
effective_date, metadata).

The Qdrant adapter must return `RetrievalResult` objects. Answers relying on
retrieved context must pass through `CitationEnforcer` when citation policy is
active.

---

## Mock API Schemas And Adapter

`mock_api_schemas/` contains production-like request/response envelopes for:

- **container_tracking** — track a container by number
- **booking_status** — check booking confirmation status
- **support_ticket** — create a support ticket

All responses follow the platform envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "mock-request-id"
}
```

PR-020 adds a deterministic local adapter in
`agents/customer_service/mock_api/`. It implements the platform `ToolExecutor`
interface for the customer-service tools without making external HTTP calls.

Future graph wiring must compose this executor behind `ToolGateway` policy and
tool call audit before any production-like workflow uses it.

---

## n8n / Zalo Integration (Future)

`n8n/zalo_webhook_payload.example.json` shows the raw Zalo OA webhook event
shape that n8n receives from the Zalo platform.

`n8n/runtime_api_request.example.json` shows the normalized `RuntimeRequest`
that n8n constructs from the Zalo event before calling the Runtime API.

A future n8n/Zalo facade endpoint (PR-021) will keep the route handler thin and
delegate webhook normalization and validation to platform packages.

---

## What Is Not Implemented

- No real Qdrant adapter or Qdrant connection
- No real production API calls
- No real LLM calls
- No runtime route changes
- No database persistence
- No Docker deployment
- No n8n workflow wiring

Follow-up PRs can add each integration independently while keeping platform
packages reusable and route handlers thin.

---

## Follow-up PRs

| PR | Goal |
|---|---|
| PR-019 | Qdrant Retriever Adapter |
| PR-020 | Production-like Mock API Adapter |
| PR-021 | n8n/Zalo Facade Endpoint |
