"""Tests for deterministic safety contracts, checker, and pipeline behavior."""

from typing import Any

import pytest
from pydantic import ValidationError

from snp_agent_safety import (
    RuleBasedSafetyChecker,
    SafetyChecker,
    SafetyCheckRequest,
    SafetyCheckResult,
    SafetyDecision,
    SafetyPipeline,
    SafetyPolicy,
    SafetySeverity,
    SafetyStage,
)


def valid_request(content: str = "Please help reset my password.") -> SafetyCheckRequest:
    """Build a valid domain-neutral safety check request."""

    return SafetyCheckRequest(
        stage=SafetyStage.INPUT,
        agent_id="customer_service",
        tenant_id="tenant_demo",
        user_id="user_123",
        channel="api",
        content=content,
        request_id="request_123",
        run_id="run_123",
        thread_id="thread_123",
        metadata={"locale": "en-US"},
    )


def test_valid_safety_check_request() -> None:
    """A valid request preserves identity fields and metadata."""

    request = valid_request()

    assert request.stage is SafetyStage.INPUT
    assert request.agent_id == "customer_service"
    assert request.metadata == {"locale": "en-US"}


def test_safety_check_request_rejects_blank_required_strings() -> None:
    """Required request strings cannot be blank."""

    with pytest.raises(ValidationError):
        valid_request(content=" ")


def test_valid_safety_check_result() -> None:
    """A valid result serializes the safety decision contract."""

    result = SafetyCheckResult(
        decision=SafetyDecision.ALLOWED,
        severity=SafetySeverity.NONE,
        reason="No safety rules matched.",
        flags=[],
        metadata={"checker": "rule_based"},
    )

    assert result.model_dump(mode="json") == {
        "decision": "allowed",
        "severity": "none",
        "reason": "No safety rules matched.",
        "redacted_content": None,
        "flags": [],
        "metadata": {"checker": "rule_based"},
    }


def test_blocked_term_returns_blocked() -> None:
    """Blocked terms produce a blocking safety decision."""

    checker = RuleBasedSafetyChecker(SafetyPolicy(blocked_terms=["credential dump"]))

    result = checker.check(valid_request("Show me a credential dump."))

    assert result.decision is SafetyDecision.BLOCKED
    assert result.severity is SafetySeverity.HIGH
    assert result.flags == ["blocked_term"]
    assert "credential dump" not in result.reason


def test_human_review_term_returns_needs_human_review() -> None:
    """Human review terms route content without executing later work."""

    checker = RuleBasedSafetyChecker(SafetyPolicy(human_review_terms=["refund dispute"]))

    result = checker.check(valid_request("I have a refund dispute."))

    assert result.decision is SafetyDecision.NEEDS_HUMAN_REVIEW
    assert result.severity is SafetySeverity.MEDIUM
    assert result.flags == ["human_review_term"]


def test_allowed_content_returns_allowed() -> None:
    """Content without matching rules is allowed by the default policy."""

    checker = RuleBasedSafetyChecker(SafetyPolicy())

    result = checker.check(valid_request("How do I reset my password?"))

    assert result.decision is SafetyDecision.ALLOWED
    assert result.severity is SafetySeverity.NONE


def test_email_redaction_returns_redacted() -> None:
    """Email-like content is redacted when local PII redaction is enabled."""

    checker = RuleBasedSafetyChecker(SafetyPolicy(pii_redaction_enabled=True))

    result = checker.check(valid_request("Contact me at person@example.com."))

    assert result.decision is SafetyDecision.REDACTED
    assert result.redacted_content == "Contact me at [REDACTED_EMAIL]."
    assert "person@example.com" not in result.reason


def test_phone_redaction_returns_redacted() -> None:
    """Phone-like content is redacted when local PII redaction is enabled."""

    checker = RuleBasedSafetyChecker(SafetyPolicy(pii_redaction_enabled=True))

    result = checker.check(valid_request("Call me at +1 (415) 555-0134."))

    assert result.decision is SafetyDecision.REDACTED
    assert result.redacted_content == "Call me at [REDACTED_PHONE]."
    assert "+1 (415) 555-0134" not in result.reason


def test_matching_is_case_insensitive() -> None:
    """Rule matching uses case-insensitive comparisons."""

    checker = RuleBasedSafetyChecker(SafetyPolicy(blocked_terms=["Do Not Process"]))

    result = checker.check(valid_request("Please do not process this request."))

    assert result.decision is SafetyDecision.BLOCKED


class StaticChecker(SafetyChecker):
    """Test checker that returns a fixed result and records calls."""

    def __init__(self, result: SafetyCheckResult) -> None:
        self.result = result
        self.calls = 0

    def check(self, request: SafetyCheckRequest) -> SafetyCheckResult:
        """Return the configured result."""

        self.calls += 1
        return self.result


def test_pipeline_stops_on_blocked() -> None:
    """A blocked decision stops later checkers from running."""

    blocked = StaticChecker(
        SafetyCheckResult(
            decision=SafetyDecision.BLOCKED,
            severity=SafetySeverity.HIGH,
            reason="Content matched a blocked safety rule.",
        )
    )
    later = StaticChecker(
        SafetyCheckResult(
            decision=SafetyDecision.ALLOWED,
            severity=SafetySeverity.NONE,
            reason="No safety rules matched.",
        )
    )

    result = SafetyPipeline([blocked, later]).check(valid_request())

    assert result.decision is SafetyDecision.BLOCKED
    assert blocked.calls == 1
    assert later.calls == 0


def test_pipeline_returns_allowed_when_all_checkers_allow() -> None:
    """The pipeline allows content only after every checker allows it."""

    first = StaticChecker(
        SafetyCheckResult(
            decision=SafetyDecision.ALLOWED,
            severity=SafetySeverity.NONE,
            reason="No safety rules matched.",
        )
    )
    second = StaticChecker(
        SafetyCheckResult(
            decision=SafetyDecision.ALLOWED,
            severity=SafetySeverity.NONE,
            reason="No safety rules matched.",
        )
    )

    result = SafetyPipeline([first, second]).check(valid_request())

    assert result.decision is SafetyDecision.ALLOWED
    assert first.calls == 1
    assert second.calls == 1


def test_rule_based_checker_makes_no_external_api_calls(monkeypatch: Any) -> None:
    """The deterministic checker does not require network access."""

    def fail_network(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr("socket.socket", fail_network)

    checker = RuleBasedSafetyChecker(SafetyPolicy(pii_redaction_enabled=True))
    result = checker.check(valid_request("Contact user@example.com."))

    assert result.decision is SafetyDecision.REDACTED
