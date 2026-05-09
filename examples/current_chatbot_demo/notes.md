# Notes

This example is intentionally documentation and schema only.

## Future Wiring

- PR-018 can wire this reference project to the current customer-service agent
  structure without adding production integrations.
- PR-019 can add a Qdrant retriever adapter behind the `Retriever` interface.
- PR-020 can add production-like mock API adapters behind tool execution
  contracts.
- PR-021 can add an n8n/Zalo facade endpoint while keeping runtime route
  handlers thin.

## Boundaries

- Retrieval must return platform `RetrievalResult` objects.
- Answers that rely on retrieval must use citation enforcement.
- Tool calls must flow through Tool Gateway policy and audit wrappers.
- Secrets belong in environment variables and must not appear in examples.
