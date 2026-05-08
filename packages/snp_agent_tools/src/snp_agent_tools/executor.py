"""Abstract interface for future tool execution adapters."""

from abc import ABC, abstractmethod

from snp_agent_tools.execution import ToolExecutionRequest, ToolExecutionResult


class ToolExecutor(ABC):
    """Interface implemented by concrete tool execution adapters."""

    @abstractmethod
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute a tool request and return a structured result."""
