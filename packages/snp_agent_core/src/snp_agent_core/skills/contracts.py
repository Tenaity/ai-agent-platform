"""Domain-neutral skill metadata contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillStep(BaseModel):
    """One documented step in a reusable workflow capability."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Stable step identifier.")
    title: str = Field(..., description="Human-readable step title.")
    description: str = Field(..., description="Step intent and expected behavior.")

    @field_validator("id", "title", "description")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        """Reject blank strings and trim surrounding whitespace."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped


class SkillSpec(BaseModel):
    """Metadata-only description of a reusable agent workflow template.

    Skills are capability templates. They describe inputs, outputs, and ordered
    workflow steps, but PR-026 does not execute arbitrary code from skill files.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Stable skill identifier.")
    name: str = Field(..., description="Human-readable skill name.")
    description: str = Field(..., description="Skill purpose.")
    version: str = Field(..., description="Skill metadata version.")
    domain: str = Field(..., description="Primary domain or capability area.")
    tags: list[str] = Field(default_factory=list, description="Search and grouping tags.")
    steps: list[SkillStep] = Field(..., description="Ordered workflow steps.")
    inputs: dict[str, str] = Field(
        default_factory=dict,
        description="Named input descriptions.",
    )
    outputs: dict[str, str] = Field(
        default_factory=dict,
        description="Named output descriptions.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Serializable metadata safe for logs and clients.",
    )

    @field_validator("id", "name", "description", "version", "domain")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        """Reject blank strings and trim surrounding whitespace."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        """Trim tags and reject blank tag entries."""

        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("tags must not contain blank values")
        return normalized

    @field_validator("steps")
    @classmethod
    def require_steps(cls, values: list[SkillStep]) -> list[SkillStep]:
        """Require at least one documented step."""

        if not values:
            raise ValueError("steps must not be empty")
        return values
