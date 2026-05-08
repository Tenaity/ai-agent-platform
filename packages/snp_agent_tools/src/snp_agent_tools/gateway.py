"""Policy-only ToolGateway skeleton.

This gateway decides whether a registered tool may be used. It intentionally
does not execute tools, call external APIs, or own integration clients.
"""

from snp_agent_tools.errors import ToolNotFoundError
from snp_agent_tools.policy import (
    ToolAccessDecision,
    ToolAccessRequest,
    ToolAccessResult,
    ToolPolicy,
)
from snp_agent_tools.registry import ToolRegistry


class ToolGateway:
    """Evaluate tool access requests against registered specs and policy."""

    def __init__(self, registry: ToolRegistry, policy: ToolPolicy) -> None:
        """Create a policy-only gateway from a registry and static policy."""

        self._registry = registry
        self._policy = policy

    def check_access(self, request: ToolAccessRequest) -> ToolAccessResult:
        """Return the policy decision for a requested tool without executing it."""

        try:
            spec = self._registry.get(request.tool_name)
        except ToolNotFoundError:
            return ToolAccessResult(
                decision=ToolAccessDecision.DENIED,
                reason=f"Tool '{request.tool_name}' is not registered.",
            )

        if spec.name in self._policy.denied_tools:
            return ToolAccessResult(
                decision=ToolAccessDecision.DENIED,
                reason=f"Tool '{spec.name}' is denied by policy.",
                required_scopes=spec.required_scopes,
            )

        if spec.name not in self._policy.allowed_tools:
            return ToolAccessResult(
                decision=self._policy.default_decision,
                reason=f"Tool '{spec.name}' is not in the policy allowlist.",
                required_scopes=spec.required_scopes,
            )

        user_scopes = set(request.user_scopes)
        missing_scopes = [scope for scope in spec.required_scopes if scope not in user_scopes]
        if missing_scopes:
            return ToolAccessResult(
                decision=ToolAccessDecision.DENIED,
                reason=f"Tool '{spec.name}' is missing required scopes.",
                required_scopes=spec.required_scopes,
                missing_scopes=missing_scopes,
            )

        if spec.approval_required or spec.name in self._policy.approval_required_tools:
            return ToolAccessResult(
                decision=ToolAccessDecision.REQUIRES_APPROVAL,
                reason=f"Tool '{spec.name}' requires approval before execution.",
                required_scopes=spec.required_scopes,
                approval_required=True,
            )

        return ToolAccessResult(
            decision=ToolAccessDecision.ALLOWED,
            reason=f"Tool '{spec.name}' is allowed by policy.",
            required_scopes=spec.required_scopes,
        )
