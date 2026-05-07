"""File-backed agent registry for local runtime API discovery."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from runtime_api.errors import AgentNotFoundError
from snp_agent_core.contracts import AgentManifest


class AgentSummary(BaseModel):
    """Basic agent metadata returned by discovery endpoints."""

    id: str = Field(..., description="Stable agent identifier.")
    version: str = Field(..., description="Agent behavior version.")
    owner: str = Field(..., description="Owning team or accountable maintainer.")
    domain: str = Field(..., description="Business or product domain for this agent.")


class FileAgentRegistry:
    """Load validated agent manifests from `agents/*/agent.yaml`."""

    def __init__(self, agents_root: Path) -> None:
        """Create a registry rooted at the repository's `agents` directory."""

        self._agents_root = agents_root

    @classmethod
    def from_runtime_package(cls) -> "FileAgentRegistry":
        """Build the default registry using the repo root inferred from this package."""

        repo_root = Path(__file__).resolve().parents[5]
        return cls(agents_root=repo_root / "agents")

    def list_agents(self) -> list[AgentSummary]:
        """Return validated agent summaries sorted by stable agent identifier."""

        manifests = [self._load_manifest(path) for path in self._manifest_paths()]
        return sorted(
            (
                AgentSummary(
                    id=manifest.id,
                    version=manifest.version,
                    owner=manifest.owner,
                    domain=manifest.domain,
                )
                for manifest in manifests
            ),
            key=lambda summary: summary.id,
        )

    def get_manifest(self, agent_id: str) -> AgentManifest:
        """Return a validated manifest or raise a structured not-found error."""

        manifest_path = self._agents_root / agent_id / "agent.yaml"
        if not manifest_path.exists():
            raise AgentNotFoundError(agent_id=agent_id)
        return self._load_manifest(manifest_path)

    def _manifest_paths(self) -> list[Path]:
        """Find candidate manifest files under the registry root."""

        if not self._agents_root.exists():
            return []
        return sorted(self._agents_root.glob("*/agent.yaml"))

    def _load_manifest(self, manifest_path: Path) -> AgentManifest:
        """Read YAML and validate it as an `AgentManifest`."""

        with manifest_path.open() as manifest_file:
            loaded = yaml.safe_load(manifest_file)

        if not isinstance(loaded, dict):
            raise ValueError(f"Agent manifest must be a mapping: {manifest_path}")

        manifest_data: dict[str, Any] = loaded
        return AgentManifest.model_validate(manifest_data)
