"""Import tests for public core package exports."""

from snp_agent_core import __version__
from snp_agent_core.contracts import AgentManifest, RuntimeHealth
from snp_agent_core.errors import PlatformError


def test_public_imports_are_available() -> None:
    """Public core package imports remain available for apps and packages."""

    assert __version__ == "0.1.0"
    assert AgentManifest.__name__ == "AgentManifest"
    assert RuntimeHealth(status="ok").status == "ok"
    assert issubclass(PlatformError, Exception)
