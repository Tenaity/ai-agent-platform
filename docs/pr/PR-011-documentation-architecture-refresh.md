# PR-011 Documentation Architecture Refresh

## Summary

- Refresh README for a new engineer joining after PR-010.
- Add architecture diagrams for components, runtime request sequence, and tool
  governance policy flow.
- Add focused architecture pages for runtime flow, request sequence, and tool
  governance flow.
- Update lifecycle, checkpointing, tool, ToolGateway, and agent development docs
  to clearly distinguish implemented behavior from future capabilities.

## Scope

- Documentation only.
- `README.md`
- `docs/architecture/overview.md`
- `docs/architecture/runtime-flow.md`
- `docs/architecture/request-sequence.md`
- `docs/architecture/tool-governance-flow.md`
- `docs/agent-development-guide.md`
- `docs/tools.md`
- `docs/tool-gateway.md`
- `docs/runtime-lifecycle.md`
- `docs/checkpointing.md`

## Explicitly Not Added

- Production code changes
- Real LLM calls
- RAG
- Real tool execution
- Production Zalo, TMS, CRM, Billing, or support integrations
- Database persistence
- Memory Manager
- Safety pipeline

## Architecture Notes

- The platform is documented as an internal AI Agent Platform SDK + Runtime, not
  a single chatbot.
- `thread_id`, `request_id`, and `run_id` are documented with ownership and
  scope.
- Tool governance is documented as policy-only after PR-010.
- Future execution adapters, safety, memory, RAG, and persistence are clearly
  marked as future work.

## Tests

- `make lint`
- `make typecheck`
- `make test`
- `make eval`

## Risk

- Low. This PR changes documentation only.
- Main risk is documentation drift; diagrams and non-goals were kept aligned
  with the current code.

## Follow-up PRs

- PR-012: tool execution interface
- PR-013: safety skeleton
- PR-014: RAG contracts
- Future: fake-tool adapters, approval workflows, durable persistence, real
  integration adapters
