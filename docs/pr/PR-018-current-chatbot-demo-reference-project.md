# PR-018: Current Chatbot Demo Reference Project Wiring

## Summary

This PR expands `examples/current_chatbot_demo` from a thin skeleton into a
complete reference project structure that documents how the SNP AI Agent
Platform scaffold applies to the user's current customer-service chatbot demo.

The demo lives in `examples/` because this repository is a platform framework,
not a single chatbot implementation. All files in this PR are schemas,
documentation, and placeholder code. No production integrations are wired.

---

## Motivation

The platform now has runtime contracts, a Runtime API, a LangGraph runtime,
safety/tool/RAG packages, project templates, and a generator CLI. The next
step is to document how these pieces connect for the actual chatbot use case:
a customer-service agent powered by Zalo messaging, Qdrant retrieval, and
production-like internal API tool calls flowing through the platform boundaries.

This PR establishes that reference structure so follow-up PRs can add each
integration independently.

---

## What This PR Does

### `examples/current_chatbot_demo/`

| File | Action | Description |
|---|---|---|
| `README.md` | Updated | Full flow description, directory structure, section per subsystem |
| `architecture.md` | Updated | Mermaid boundary diagram, node table, platform boundary rules, state field table |
| `notes.md` | Updated | PR-018 scope summary, future wiring table, boundary rules, known limitations |
| `__init__.py` | Added | Makes demo importable for graph module tests |

### `examples/current_chatbot_demo/agent/`

| File | Action | Description |
|---|---|---|
| `README.md` | Updated | File table, graph shape, state schema summary, promotion path |
| `agent.yaml` | Updated | Added description, requires_audit, pii_redaction, inline comments for non-implemented fields |
| `graph.py` | Updated | INTENT constants, VALID_INTENTS frozenset, full module docstring, detailed build_graph docstring |
| `state.py` | Updated | Added retrieval_results, citations, tool_result fields with type annotations and field group docs |
| `prompts/system.md` | Updated | Domain context, numbered behavior rules, out-of-scope section |
| `prompts/rag_answer.md` | Updated | Citation rules, answer format guidelines, domain-specific example |
| `evals/eval.yaml` | Updated | 6 reference cases covering tool (×3), RAG (×2), direct_answer (×1) branches |
| `__init__.py` | Added | Package init for agent sub-module |

### `examples/current_chatbot_demo/qdrant/`

| File | Action | Description |
|---|---|---|
| `config.example.yaml` | Updated | Added score_threshold, inline comments, env variable guidance |
| `payload_schema.example.json` | Updated | Added language field, richer metadata (tags, last_reviewed), comment field |

### `examples/current_chatbot_demo/mock_api_schemas/`

| File | Action | Description |
|---|---|---|
| `container_tracking.request.example.json` | Updated | Descriptive request_id |
| `container_tracking.response.example.json` | Updated | Added container_type, terminal, next_event, vessel, voyage |
| `booking_status.request.example.json` | Updated | Descriptive request_id |
| `booking_status.response.example.json` | Updated | Added shipper, consignee, ports, cutoffs, container counts |
| `support_ticket.request.example.json` | Updated | Added channel, priority, related_reference, detailed description |
| `support_ticket.response.example.json` | Updated | Added assigned_queue, estimated_response_hours, customer_reference |

### `examples/current_chatbot_demo/n8n/`

| File | Action | Description |
|---|---|---|
| `zalo_webhook_payload.example.json` | Updated | Vietnamese message, realistic IDs, user_id_by_app, comment field |
| `runtime_api_request.example.json` | Updated | Richer metadata (workflow, oa_id, received_at), comment field |

### `tests/`

| File | Action | Description |
|---|---|---|
| `test_chatbot_demo_structure.py` | Added | 30+ tests: file presence, JSON validity, response envelopes, agent.yaml content, graph module import and behavior |

### `examples/__init__.py`

Added to make `examples` a Python package, enabling `from examples.current_chatbot_demo.agent.graph import ...` in tests.

---

## Explicitly Not Added

- No real Qdrant adapter or Qdrant connection
- No real production API calls
- No real LLM calls
- No runtime route changes
- No database persistence
- No Docker deployment
- No n8n workflow wiring
- No agents/customer_service changes (reference is in examples only)

---

## Architecture Notes

The reference graph shape:

```
Input
→ Safety precheck         (SafetyPipeline.check_input)
→ Intent routing          (rag / tool / direct_answer)
→ RAG branch              (future Qdrant retriever → RetrievalResult + citations)
→ Tool branch             (future mock API adapters → ToolGateway → audit)
→ Answer formatting       (CitationEnforcer when citations required)
→ RuntimeResponse
```

All example files remain in `examples/`. Packages must not import examples.
Route handlers are unchanged.

---

## Platform Boundary Rules (Enforced by This PR's Documentation)

| Boundary | Rule |
|---|---|
| Safety | Must be an explicit runtime node, not prompt-only behavior |
| Retrieval | Must implement `Retriever`, return `RetrievalResult`, enforce citations |
| Tools | Must flow through `ToolGateway` → `ToolExecutor` → `ToolCallRecord` |
| n8n/Zalo | Route handler must stay thin; normalization delegated to packages |
| Secrets | Environment variables only; no secrets in example files |

---

## Tests

- `tests/test_chatbot_demo_structure.py` — PR-018 specific (new)
- `tests/test_templates_structure.py` — already covers 6 required demo files (unchanged)

Run all tests:

```bash
make test
```

---

## Follow-up PRs

| PR | Scope |
|---|---|
| PR-019 | Qdrant Retriever Adapter — implement `Retriever` backed by Qdrant |
| PR-020 | Production-like Mock API Adapter — implement `ToolExecutor` with audited mock responses |
| PR-021 | n8n/Zalo Facade Endpoint — thin HTTP route for Zalo webhook normalization |

---

## Acceptance Criteria

- [x] `make lint` passes
- [x] `make typecheck` passes
- [x] `make test` passes
- [x] `make eval` passes
- [x] All required demo files present (verified by `test_chatbot_demo_structure.py` and `test_templates_structure.py`)
- [x] No real secrets, no real integrations, no runtime route changes
- [x] `examples/` remain separate from framework packages
