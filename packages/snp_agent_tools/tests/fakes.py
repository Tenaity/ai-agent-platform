"""Fake tool executors for tests."""

from snp_agent_tools import ToolExecutionRequest, ToolExecutionResult, ToolExecutionStatus
from snp_agent_tools.executor import ToolExecutor


class FakeToolExecutor(ToolExecutor):
    """Deterministic test executor with optional failure modes."""

    def __init__(
        self,
        *,
        should_fail: bool = False,
        should_timeout: bool = False,
        latency_ms: int | None = None,
    ) -> None:
        """Create a fake executor."""

        self.should_fail = should_fail
        self.should_timeout = should_timeout
        self.latency_ms = latency_ms
        self.requests: list[ToolExecutionRequest] = []

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Return deterministic output or simulate a failure mode."""

        self.requests.append(request)
        if self.should_fail:
            raise RuntimeError("sensitive fake stack detail")
        if self.should_timeout:
            return ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.TIMED_OUT,
                error="Tool execution timed out.",
                latency_ms=self.latency_ms,
            )
        return ToolExecutionResult(
            tool_name=request.tool_name,
            status=ToolExecutionStatus.SUCCEEDED,
            output={"ok": True, "input": request.input},
            latency_ms=self.latency_ms,
        )
