"""Safety pipeline orchestration."""

from snp_agent_safety.checker import SafetyChecker
from snp_agent_safety.contracts import (
    SafetyCheckRequest,
    SafetyCheckResult,
    SafetyDecision,
    SafetySeverity,
)


class SafetyPipeline:
    """Run safety checkers in order and stop on the first non-allowed decision.

    The current skeleton favors explicit, simple behavior: blocked and human
    review results stop the pipeline, and redaction also returns immediately
    with the redacted content. Later PRs can add richer content rewriting and
    continuation semantics without changing the checker contract.
    """

    def __init__(self, checkers: list[SafetyChecker]) -> None:
        """Create a safety pipeline with ordered checker instances."""

        self._checkers = checkers

    def check(self, request: SafetyCheckRequest) -> SafetyCheckResult:
        """Evaluate checkers in order and return the first actionable decision."""

        for checker in self._checkers:
            result = checker.check(request)
            if result.decision in {
                SafetyDecision.BLOCKED,
                SafetyDecision.NEEDS_HUMAN_REVIEW,
                SafetyDecision.REDACTED,
            }:
                return result

        return SafetyCheckResult(
            decision=SafetyDecision.ALLOWED,
            severity=SafetySeverity.NONE,
            reason="All safety checks allowed the content.",
        )
