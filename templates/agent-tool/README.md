# Agent Tool Template

Use this template for action-oriented agents that need tool capability specs,
policy checks, execution wrappers, and audit shape. It does not include real
external APIs.

## Intended Use

- ToolSpec-first tool modeling.
- ToolGateway policy checks.
- PolicyAwareToolExecutor and AuditAwareToolExecutor composition.
- Fake-tool tests before production adapters.
