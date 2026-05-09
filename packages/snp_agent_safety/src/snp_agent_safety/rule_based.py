"""Deterministic rule-based safety checker."""

from __future__ import annotations

import re

from snp_agent_safety.checker import SafetyChecker
from snp_agent_safety.contracts import (
    SafetyCheckRequest,
    SafetyCheckResult,
    SafetyDecision,
    SafetySeverity,
)
from snp_agent_safety.policy import SafetyPolicy

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d[\d .()\-]{7,}\d)(?!\w)",
    re.IGNORECASE,
)


class RuleBasedSafetyChecker(SafetyChecker):
    """Apply simple local safety rules without external services."""

    def __init__(self, policy: SafetyPolicy | None = None) -> None:
        """Create a checker with a deterministic local policy."""

        self._policy = policy or SafetyPolicy()

    def check(self, request: SafetyCheckRequest) -> SafetyCheckResult:
        """Return the first matching local safety decision for the content."""

        lowered_content = request.content.casefold()

        if self._contains_any(lowered_content, self._policy.blocked_terms):
            return SafetyCheckResult(
                decision=SafetyDecision.BLOCKED,
                severity=SafetySeverity.HIGH,
                reason="Content matched a blocked safety rule.",
                flags=["blocked_term"],
            )

        if self._contains_any(lowered_content, self._policy.human_review_terms):
            return SafetyCheckResult(
                decision=SafetyDecision.NEEDS_HUMAN_REVIEW,
                severity=SafetySeverity.MEDIUM,
                reason="Content matched a human review safety rule.",
                flags=["human_review_term"],
            )

        if self._policy.pii_redaction_enabled:
            redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", request.content)
            redacted = PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)
            if redacted != request.content:
                return SafetyCheckResult(
                    decision=SafetyDecision.REDACTED,
                    severity=SafetySeverity.LOW,
                    reason="Content was redacted by a local PII rule.",
                    redacted_content=redacted,
                    flags=["pii_redacted"],
                )

        return SafetyCheckResult(
            decision=self._policy.default_decision,
            severity=SafetySeverity.NONE,
            reason="No safety rules matched.",
        )

    @staticmethod
    def _contains_any(lowered_content: str, terms: list[str]) -> bool:
        """Return whether any non-blank term is present in already folded content."""

        return any(term.strip().casefold() in lowered_content for term in terms if term.strip())
