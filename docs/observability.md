# Observability

PR-005 adds the first LangSmith tracing skeleton. Observability is a platform
boundary: runtime code attaches common metadata to graph executions so domain
agents do not need to know how tracing is configured.

## LangSmith Settings

Tracing is disabled by default. Local development and tests must pass without a
LangSmith API key.

Environment variables:

- `LANGSMITH_TRACING`: set to `true` to enable LangSmith environment setup.
- `LANGSMITH_ENDPOINT`: optional LangSmith endpoint override.
- `LANGSMITH_API_KEY`: LangSmith API key. Never commit real values.
- `LANGSMITH_PROJECT`: LangSmith project name.
- `SNP_TRACE_SAMPLE_RATE`: future sampling control, from `0.0` to `1.0`.

`configure_langsmith()` only sets LangSmith environment variables when tracing
is explicitly enabled. It does not print secrets and does not contact the
network.

## Trace Metadata

Every graph execution should receive standard metadata:

- `request_id`
- `tenant_id`
- `channel`
- `user_id`
- `thread_id`
- `agent_id`
- `agent_version`
- `domain`

These keys support trace filtering, ownership, and incident investigation. They
must remain domain-neutral and safe to attach to runtime traces.
