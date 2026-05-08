# Tool Specifications and Registry

PR-009 introduced domain-neutral tool contracts before tool execution exists.
The goal is to describe available capabilities in a reusable, testable shape.
PR-010 added a policy-only ToolGateway that uses these specs to make access
decisions.

## `ToolSpec`

`ToolSpec` defines a tool capability. It includes:

- stable name and description
- risk level (`low`, `medium`, `high`, `critical`)
- execution mode (`read`, `write`, `side_effect`)
- input and output schemas
- required authorization scopes
- approval, timeout, tags, and metadata fields

`ToolSpec` does not include Python callables, provider clients, credentials, or
transport details. It is a Pydantic contract with `extra="forbid"` so tools
remain explicit at package boundaries.

## `ToolRegistry`

`ToolRegistry` stores available `ToolSpec` objects in memory. It supports:

- `register(spec)`
- `get(name)`
- `list()`
- `exists(name)`

Duplicate names raise `DuplicateToolError`. Unknown names raise
`ToolNotFoundError`.

The registry is intentionally in-memory for now. It does not persist tool
definitions, execute tools, call APIs, or enforce runtime policies.

## Customer Service Samples

The customer service sample agent defines example specs in
`agents/customer_service/tools.py`:

- `tracking_container`
- `check_booking_status`
- `create_support_ticket`

These are specs only. They do not call real TMS, CRM, billing, or support
systems.

## Future Tool Gateway

PR-010 adds a policy-only `ToolGateway` skeleton. It uses `ToolSpec` metadata
and `ToolPolicy` to decide whether an agent may use a tool. The gateway returns
`allowed`, `denied`, or `requires_approval`, but still does not execute tools.

The future execution-capable Tool Gateway will be the only approved path for
tool execution. It will use `ToolSpec` metadata to validate inputs, audit calls,
and route to fake or real integrations after policy allows access.

PR-009 and PR-010 deliberately do not add:

- actual tool execution
- RAG
- Memory Manager
- Safety pipeline
- real LLM calls
- real third-party integrations
- database persistence

See [tool-gateway.md](tool-gateway.md) for the policy decision skeleton.
See [architecture/tool-governance-flow.md](architecture/tool-governance-flow.md)
for the policy flow diagram.
