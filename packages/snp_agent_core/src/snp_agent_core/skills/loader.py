"""YAML loader for metadata-only skill specs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from snp_agent_core.skills.contracts import SkillSpec
from snp_agent_core.skills.registry import SkillRegistry


def load_skill_file(path: Path) -> SkillSpec:
    """Load and validate one `skill.yaml` file without executing code."""

    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Skill file '{path}' must contain a YAML mapping.")
    return SkillSpec.model_validate(raw)


def load_skills_from_directory(skills_root: Path) -> SkillRegistry:
    """Load every `*/skill.yaml` under a skills directory into a registry."""

    registry = SkillRegistry()
    if not skills_root.exists():
        return registry

    for skill_file in sorted(skills_root.glob("*/skill.yaml")):
        registry.register(load_skill_file(skill_file))
    return registry
