# Current Chatbot Demo Agent

This directory is a reference agent project shape for the current chatbot demo.
It shows how a concrete agent can follow the platform scaffold while remaining
separate from framework packages.

## Purpose

This agent project is **documentation-oriented placeholder code**. It defines
the intended graph structure, state schema, prompt shapes, and eval cases that
the production customer-service chatbot will eventually implement.

No real Qdrant retrieval, real production API call, real LLM call, or runtime
registration is implemented here.

## File Reference

| File | Purpose |
|---|---|
| `agent.yaml` | Reference agent manifest: id, version, runtime, tools, retrieval, safety, eval |
| `graph.py` | Placeholder graph class documenting the intended node order |
| `state.py` | Typed state TypedDict for the reference graph |
| `prompts/system.md` | System prompt template for the customer-service agent |
| `prompts/rag_answer.md` | Answer prompt for RAG-grounded responses with citation rules |
| `evals/eval.yaml` | Reference eval cases covering tool branch and RAG branch routing |

## Intended Graph Shape

```
input
  → safety_precheck
  → intent_routing
  → rag_branch_future_qdrant    (when intent = rag)
  → tool_branch_future_mock_api  (when intent = tool)
  → answer_formatting
  → runtime_response
```

Each node is a placeholder until the corresponding integration PR lands:
- Qdrant retriever: PR-019
- Mock API adapters: PR-020

## State Schema

`state.py` defines `CurrentChatbotDemoState` as a `TypedDict` with `total=False`
so fields can be added incrementally as the demo evolves. Key fields:

- `tenant_id`, `user_id`, `channel`, `thread_id`, `request_id` — identity/routing
- `message` — raw user input
- `safety_decision` — output of safety precheck
- `intent` — classified routing decision
- `retrieval_query`, `retrieval_results`, `citations` — RAG branch state
- `tool_name`, `tool_result` — tool branch state
- `answer` — final formatted response

## Promotion Path

When ready for production:

1. Create a versioned agent under `agents/customer_service/` using the
   `agent-full-demo` template as a starting point.
2. Add real integration tests and regression datasets under
   `datasets/customer_service/`.
3. Register the agent in the Runtime API agent registry.
4. Run `make lint`, `make typecheck`, `make test`, and `make eval`.
