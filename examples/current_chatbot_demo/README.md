# Current Chatbot Demo Reference Project

This directory is a **reference project** that documents how the SNP AI Agent
Platform scaffold applies to the user's current customer-service chatbot demo.
It is project structure, schemas, documentation, and deterministic local demo
wiring — not production runtime integration code.

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
      → RAG branch (in-memory fixtures now, future Qdrant retriever adapter)
          → RetrievalResult + CitationEnforcer
      → Tool branch (production-like mock API adapters)
          → ToolGateway policy check → executor → audit record
      → Answer formatting node
  → RuntimeResponse returned to n8n
  → n8n formats reply and sends back to Zalo user
```

See `architecture.md` for the full boundary diagram and node-level description.

---

## Telegram Local Demo

PR-022 adds `apps/telegram-worker`, a local long-polling worker for Telegram
BotFather bots. PR-023 turns it into a local showcase cockpit. PR-024 adds
local human-in-the-loop approval commands. The worker uses Telegram
`getUpdates`, normalizes text updates and showcase commands, calls the Runtime
API when a command maps to agent behavior, and sends answers back with
`sendMessage`.

This mode is useful for local chatbot testing because it does not require
public HTTPS, a webhook endpoint, deployment, or production integrations.

Run the Runtime API and worker locally:

```bash
make run-runtime-api
curl http://localhost:8000/v1/agents
make run-telegram-worker
```

Confirm `TELEGRAM_AGENT_ID` matches one of the returned agent ids before
starting the worker. See [Telegram local demo](../../docs/telegram-local-demo.md)
for setup details.

Start with `/showcase` in Telegram to get the recommended demo script. Commands
such as `/rag`, `/tool container`, `/booking`, and `/ticket` route through the
Runtime API. `/human`, `/approve`, `/reject`, and `/approvals` are local demo
commands backed by reusable in-memory approval contracts. Future capability
commands such as `/memo`, `/mcp`, `/a2a`, and `/deepagent` return local
placeholder responses until their platform PRs exist.

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

The customer-service demo graph in `agents/customer_service/graph.py` now wires
this deterministic local shape:

```
Input
→ Safety precheck         (SafetyPipeline: rule-based + optional PII redaction)
→ Intent routing          (deterministic keyword rules)
→ RAG branch              (InMemoryRetriever fixtures → RetrievalResult + citations)
→ Tool branch             (mock API adapters → ToolGateway → audit)
→ Answer formatting       (CitationEnforcer when citations required)
→ RuntimeResponse
```

The example `agent/graph.py` remains a documentation sketch, while the runnable
demo graph lives under `agents/customer_service`. Tests use local fixtures and
the production-like mock API adapter only.

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
PR-021 composes it behind `ToolGateway`, `PolicyAwareToolExecutor`, and
`AuditAwareToolExecutor` inside the customer-service demo graph.

---

## n8n / Zalo Integration (Future)

`n8n/zalo_webhook_payload.example.json` shows the raw Zalo OA webhook event
shape that n8n receives from the Zalo platform.

`n8n/runtime_api_request.example.json` shows the normalized `RuntimeRequest`
that n8n constructs from the Zalo event before calling the Runtime API.

A future n8n/Zalo facade endpoint (PR-023) will keep the route handler thin and
delegate webhook normalization and validation to platform packages.

---

## What Is Not Implemented

- No real Qdrant adapter or Qdrant connection
- No real production API calls
- No real LLM calls
- No runtime route changes
- No database persistence
- No Docker deployment
- No webhook endpoint
- No n8n workflow wiring
- No durable human approval persistence yet

Follow-up PRs can add each integration independently while keeping platform
packages reusable and route handlers thin.

---

## Follow-up PRs

| PR | Goal |
|---|---|
| PR-019 | Qdrant Retriever Adapter |
| PR-020 | Production-like Mock API Adapter |
| PR-021 | Wire Current Chatbot Demo Graph |
| PR-022 | Telegram Polling Worker Local Demo |
| PR-023 | Telegram Showcase Command Router |
| PR-024 | Human-in-the-loop Showcase |
