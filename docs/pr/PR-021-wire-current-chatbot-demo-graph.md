# PR-021: Wire Current Chatbot Demo Graph

## Summary

Wires the customer-service demo LangGraph workflow through deterministic local
boundaries:

- safety precheck with `SafetyPipeline`
- keyword intent routing
- policy-question RAG branch using `InMemoryRetriever` fixtures
- citation enforcement with `CitationEnforcer`
- tool branches for container tracking, booking status, and support tickets
- governed mock API execution through `ToolGateway`, `PolicyAwareToolExecutor`,
  and `AuditAwareToolExecutor`
- deterministic fallback answer for existing eval compatibility

No real LLM, production API, Qdrant server, Zalo/n8n endpoint, document
ingestion, or persistence is added.

## Scope

- `agents/customer_service/state.py`
- `agents/customer_service/intent.py`
- `agents/customer_service/graph.py`
- `agents/customer_service/tests/test_graph.py`
- `examples/current_chatbot_demo/*` documentation
- platform documentation updates

## Explicitly Not Added

- No real LLM calls
- No real production API calls
- No live Qdrant graph dependency
- No Zalo or n8n route
- No document ingestion
- No database persistence
- No runtime route changes
- No external service calls in tests

## Architecture Notes

The graph composes package-level abstractions from agent code. Packages remain
domain-neutral and do not import agents or examples.

The RAG branch uses `InMemoryRetriever` and customer-service fixture chunks so
CI remains local and deterministic. `QdrantRetriever` remains available as an
adapter but is not required by the graph tests.

The tool branch uses the production-like mock API adapter introduced in PR-020,
but execution still flows through ToolGateway policy and audit wrappers. The
support-ticket tool spec remains approval-aware; the demo graph registers a
local mock-only copy that can execute deterministically for tests.

## Tests

Added graph tests covering:

- policy question routes to RAG branch with citations
- container query routes to container tracking tool branch
- booking query routes to booking status tool branch
- support request routes to support ticket tool branch
- unknown question routes to fallback
- blocked safety input does not execute RAG/tool
- graph execution works through `GraphRunner`

## Risk

Low. The change is deterministic, local-only, and scoped to the customer-service
agent demo. Existing eval compatibility is preserved by keeping the hello
fallback answer for unknown input.

## Follow-Up PRs

- Wire live Qdrant retrieval into the demo graph behind explicit configuration.
- Add a thin n8n/Zalo facade endpoint without route-handler business logic.
- Add richer deterministic eval cases for RAG and tool routes.
- Add real production adapters only after auth, policy, audit, and testing
  boundaries are explicit.
