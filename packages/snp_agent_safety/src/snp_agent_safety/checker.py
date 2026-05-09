"""Safety checker interface."""

from abc import ABC, abstractmethod

from snp_agent_safety.contracts import SafetyCheckRequest, SafetyCheckResult


class SafetyChecker(ABC):
    """Abstract interface implemented by deterministic or provider-backed checkers."""

    @abstractmethod
    def check(self, request: SafetyCheckRequest) -> SafetyCheckResult:
        """Evaluate a safety request and return a safe decision."""
