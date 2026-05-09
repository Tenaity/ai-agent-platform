"""Deterministic local safety policy configuration."""

from pydantic import Field

from snp_agent_safety.contracts import SafetyBaseModel, SafetyDecision


class SafetyPolicy(SafetyBaseModel):
    """Local rule configuration for safety checks.

    This policy is intentionally deterministic. It does not call external
    moderation APIs, invoke an LLM judge, or load domain-specific integrations.
    """

    blocked_terms: list[str] = Field(
        default_factory=list,
        description="Case-insensitive terms that block content when present.",
    )
    pii_redaction_enabled: bool = Field(
        default=False,
        description="Whether simple local PII redaction patterns are applied.",
    )
    human_review_terms: list[str] = Field(
        default_factory=list,
        description="Case-insensitive terms that route content to human review.",
    )
    default_decision: SafetyDecision = Field(
        default=SafetyDecision.ALLOWED,
        description="Decision returned when no local rule matches.",
    )
