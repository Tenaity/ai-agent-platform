# PR-018: Current Chatbot Demo Reference Project Wiring

## Summary

Expand `examples/current_chatbot_demo` into a reference project structure that
shows how the scaffold applies to the user's current chatbot demo.

## Scope

- Add a reference agent structure under `examples/current_chatbot_demo/agent`.
- Add Qdrant example config and payload schema under `qdrant/`.
- Add production-like mock API request/response envelopes.
- Add n8n/Zalo webhook and Runtime API request examples.
- Update example architecture and notes.
- Add structure validation for key example files.

## Explicitly Not Added

- No real Qdrant adapter or Qdrant connection.
- No real production API calls.
- No real LLM calls.
- No runtime route changes.
- No database persistence.
- No Docker deployment.

## Architecture Notes

This example demonstrates the project shape:

```text
Input
-> Safety precheck
-> Intent routing
-> RAG branch using future Qdrant retriever
-> Tool branch using future production-like mock API adapters
-> Answer formatting
-> RuntimeResponse
```

The example remains outside framework packages. Packages must not import
examples, and route handlers remain unchanged.

## Tests

- Structure validation covers required demo files.
- JSON examples remain static schema/payload examples only.

## Risk

Low. This PR changes reference project files and docs only.

## Follow-up PRs

- PR-019 Qdrant Retriever Adapter
- PR-020 Production-like Mock API Adapter
- PR-021 n8n/Zalo Facade Endpoint

