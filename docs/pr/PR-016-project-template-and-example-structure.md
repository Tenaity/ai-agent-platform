# PR-016: Project Template and Example Structure

## Summary

Add reusable project templates and a current chatbot demo example structure so
the repository can support many agent projects instead of reading as a single
customer-service chatbot implementation.

## Scope

- Add `templates/agent-basic`.
- Add `templates/agent-rag`.
- Add `templates/agent-tool`.
- Add `templates/agent-full-demo`.
- Add `examples/current_chatbot_demo` documentation and schema examples.
- Add scaffold-template documentation.
- Update README, architecture overview, and repository agent instructions.
- Add a simple template structure test.

## Explicitly Not Added

- No real Qdrant integration.
- No real production API integrations.
- No real LLM calls.
- No production deployment.
- No new runtime behavior.
- No route handler logic.
- No database persistence.

## Architecture Notes

Templates are scaffolds, not runtime code. Examples are reference
implementations or project notes, not framework packages. Packages remain
domain-neutral and must not import examples or templates.

The current chatbot demo example documents future wiring for Runtime API,
customer-service agent, Qdrant retrieval, mocked production-like APIs, and
n8n/Zalo webhook flow without implementing those integrations.

## Tests

- `tests/test_templates_structure.py` verifies required template and example
  files exist.

## Risk

Risk is low because this PR adds static scaffold files, docs, examples, and a
structure test only. It does not change runtime behavior.

## Follow-Up PRs

- PR-017 Agent Project Generator CLI Skeleton
- PR-018 Current Chatbot Demo Reference Project Wiring
- PR-019 Qdrant Retriever Adapter
- PR-020 Production-like Mock API Adapter
- PR-021 n8n/Zalo Facade Endpoint
