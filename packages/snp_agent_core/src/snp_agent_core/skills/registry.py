"""In-memory registry for skill metadata."""

from __future__ import annotations

from snp_agent_core.skills.contracts import SkillSpec


class SkillRegistryError(RuntimeError):
    """Base error for skill registry operations."""


class SkillAlreadyRegisteredError(SkillRegistryError):
    """Raised when a skill id is registered more than once."""


class SkillNotFoundError(SkillRegistryError):
    """Raised when a skill id does not exist."""


class SkillRegistry:
    """In-memory registry for metadata-only skill specs."""

    def __init__(self) -> None:
        """Create an empty skill registry."""

        self._skills: dict[str, SkillSpec] = {}

    def register(self, spec: SkillSpec) -> None:
        """Register a skill spec, rejecting duplicate ids."""

        if spec.id in self._skills:
            raise SkillAlreadyRegisteredError(f"Skill '{spec.id}' is already registered.")
        self._skills[spec.id] = spec

    def get(self, skill_id: str) -> SkillSpec:
        """Return a skill spec by id or raise a clear error."""

        normalized = _normalize_skill_id(skill_id)
        try:
            return self._skills[normalized]
        except KeyError:
            raise SkillNotFoundError(f"Skill '{normalized}' was not found.") from None

    def list(self) -> list[SkillSpec]:
        """Return registered skills in insertion order."""

        return list(self._skills.values())

    def exists(self, skill_id: str) -> bool:
        """Return whether a skill id is registered."""

        try:
            normalized = _normalize_skill_id(skill_id)
        except ValueError:
            return False
        return normalized in self._skills


def _normalize_skill_id(skill_id: str) -> str:
    normalized = skill_id.strip()
    if not normalized:
        raise ValueError("skill_id must not be blank")
    return normalized
