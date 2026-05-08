"""Policy-aware wrapper around a tool executor interface."""

from snp_agent_tools.execution import (
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
)
from snp_agent_tools.executor import ToolExecutor
from snp_agent_tools.gateway import ToolGateway
from snp_agent_tools.policy import ToolAccessDecision, ToolAccessRequest


class PolicyAwareToolExecutor(ToolExecutor):
    """Apply ToolGateway policy before delegating to a ToolExecutor.

    Implements ``ToolExecutor`` so it can be composed with other executor
    wrappers such as ``AuditAwareToolExecutor``.
    """

    def __init__(self, gateway: ToolGateway, executor: ToolExecutor) -> None:
        """Create a policy-aware executor wrapper."""

        self._gateway = gateway
        self._executor = executor

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Check access first, then execute only when policy allows it."""

        access = self._gateway.check_access(
            ToolAccessRequest(
                agent_id=request.agent_id,
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                channel=request.channel,
                tool_name=request.tool_name,
                user_scopes=request.user_scopes,
                metadata=request.metadata,
            )
        )

        if access.decision == ToolAccessDecision.DENIED:
            return ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.DENIED,
                error=access.reason,
                metadata={"policy_decision": access.decision},
            )

        if access.decision == ToolAccessDecision.REQUIRES_APPROVAL:
            return ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.REQUIRES_APPROVAL,
                error=access.reason,
                approval_required=True,
                metadata={"policy_decision": access.decision},
            )

        try:
            return self._executor.execute(request)
        except Exception:
            return ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.FAILED,
                error="Tool execution failed.",
            )

