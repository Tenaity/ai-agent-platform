# Notes

This example is intentionally documentation, schemas, and placeholder agent
shape only.

## Future Wiring

- PR-019 can add a Qdrant retriever adapter behind the `Retriever` interface.
- PR-020 can add production-like mock API adapters behind tool execution
  contracts.
- PR-021 can add an n8n/Zalo facade endpoint while keeping runtime route
  handlers thin.

## Boundaries

- `examples/` are reference projects, not framework packages.
- Packages must not import this example.
- Retrieval must return platform `RetrievalResult` objects.
- Answers that rely on retrieval must use citation enforcement.
- Tool calls must flow through Tool Gateway policy and audit wrappers.
- Secrets belong in environment variables and must not appear in examples.

