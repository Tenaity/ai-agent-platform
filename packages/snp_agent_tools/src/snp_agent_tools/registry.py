"""In-memory registry for domain-neutral tool specifications."""

from snp_agent_tools.contracts import ToolSpec
from snp_agent_tools.errors import DuplicateToolError, ToolNotFoundError


class ToolRegistry:
    """Store available tool specs without executing tools.

    The registry is intentionally in-memory for PR-009. It provides discovery
    and validation boundaries for future Tool Gateway work without introducing
    persistence, provider clients, or execution paths.
    """

    def __init__(self) -> None:
        """Create an empty registry."""

        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        """Register a tool spec by unique name."""

        if spec.name in self._tools:
            raise DuplicateToolError(f"Tool '{spec.name}' is already registered.")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        """Return a registered tool spec by name."""

        normalized_name = name.strip()
        if normalized_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{normalized_name}' was not found.")
        return self._tools[normalized_name]

    def list(self) -> list[ToolSpec]:
        """Return registered tool specs in registration order."""

        return list(self._tools.values())

    def exists(self, name: str) -> bool:
        """Return whether a tool name is registered."""

        return name.strip() in self._tools
