"""Tests for reusable skill contracts, registry, and YAML loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from snp_agent_core.skills import (
    SkillAlreadyRegisteredError,
    SkillNotFoundError,
    SkillRegistry,
    SkillSpec,
    SkillStep,
    load_skills_from_directory,
)


def _skill(skill_id: str = "demo_skill") -> SkillSpec:
    return SkillSpec(
        id=skill_id,
        name="Demo Skill",
        description="Reusable demo workflow template.",
        version="0.1.0",
        domain="demo",
        tags=["demo"],
        inputs={"message": "User message."},
        outputs={"summary": "Workflow summary."},
        steps=[
            SkillStep(
                id="step_one",
                title="Step one",
                description="First deterministic step.",
            )
        ],
    )


def test_skill_spec_validates() -> None:
    spec = _skill()

    assert spec.id == "demo_skill"
    assert spec.steps[0].id == "step_one"


def test_skill_spec_rejects_blank_required_strings() -> None:
    with pytest.raises(ValidationError):
        SkillSpec(
            id=" ",
            name="Demo Skill",
            description="Reusable demo workflow template.",
            version="0.1.0",
            domain="demo",
            steps=[
                SkillStep(
                    id="step_one",
                    title="Step one",
                    description="First deterministic step.",
                )
            ],
        )


def test_skill_registry_rejects_duplicate_skill_id() -> None:
    registry = SkillRegistry()
    registry.register(_skill("duplicate"))

    with pytest.raises(SkillAlreadyRegisteredError):
        registry.register(_skill("duplicate"))


def test_skill_registry_rejects_unknown_skill_id() -> None:
    registry = SkillRegistry()

    with pytest.raises(SkillNotFoundError, match=r"Skill 'missing' was not found\."):
        registry.get("missing")


def test_skill_registry_lists_in_insertion_order() -> None:
    registry = SkillRegistry()
    first = _skill("first")
    second = _skill("second")

    registry.register(first)
    registry.register(second)

    assert registry.list() == [first, second]
    assert registry.exists("first") is True
    assert registry.exists("missing") is False


def test_yaml_loader_loads_sample_skills() -> None:
    registry = load_skills_from_directory(Path("skills"))

    skill_ids = [skill.id for skill in registry.list()]
    assert skill_ids == [
        "container_tracking_triage",
        "customer_service_checklist",
        "support_ticket_creation",
    ]
    assert registry.get("container_tracking_triage").steps


def test_snp_agent_core_skills_do_not_import_apps() -> None:
    package_dir = Path("packages/snp_agent_core/src/snp_agent_core/skills")
    source = "\n".join(path.read_text() for path in package_dir.glob("*.py"))

    assert "telegram_worker" not in source
    assert "apps." not in source
