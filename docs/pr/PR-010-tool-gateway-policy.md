# PR-010 ToolGateway Policy Skeleton

## Summary

- Add domain-neutral tool policy contracts in `snp_agent_tools`.
- Add a policy-only `ToolGateway` that checks registered tools against static
  allow, deny, approval, and scope rules.
- Add tests for allowed, denied, unknown, default denied, missing scope, and
  approval-required decisions.
- Document the ToolGateway boundary and future execution-adapter path.

## Scope

- `packages/snp_agent_tools`
- `tests`
- `docs`
- `.github/pull_request_template.md`
- `AGENTS.md`

## Explicitly Not Added

- Real tool execution
- Real TMS, CRM, Billing, support, or third-party integrations
- RAG
- Memory Manager
- Safety pipeline
- Real LLM calls
- Database persistence

## Architecture Notes

- `ToolSpec` defines capability metadata.
- `ToolRegistry` stores available specs in memory.
- `ToolPolicy` defines static policy configuration.
- `ToolGateway.check_access()` returns a structured policy decision only.
- Tool execution adapters will come later behind the gateway boundary.

## Tests

- Allowed tool returns `allowed`.
- Unknown tool returns `denied`.
- Explicitly denied tool returns `denied`.
- Tool outside allowlist returns the default denied decision.
- Missing required scope returns `denied`.
- Approval-required tools return `requires_approval`.
- PR-009 registry duplicate and unknown tests still pass.
- Customer service sample tool specs can be checked through the gateway.

## Risk

- Low. This PR adds contracts and deterministic in-memory policy decisions only.
- No external calls, persistence, credentials, or execution adapters are added.

## Follow-up PRs

- Add fake-tool execution adapters behind `ToolGateway`.
- Add policy audit records and runtime trace metadata.
- Add approval workflow contracts.
- Add real integration adapters only after fake-tool tests and policy enforcement
  are stable.
