"""Import tests for public core package exports."""

from snp_agent_core import __version__
from snp_agent_core.contracts import (
    AgentManifest,
    AgentRunStatus,
    Citation,
    EvalManifest,
    MemoryManifest,
    ModelPolicyManifest,
    ObservabilityManifest,
    RetrievalManifest,
    RuntimeContext,
    RuntimeHealth,
    RuntimeManifest,
    RuntimeRequest,
    RuntimeResponse,
    SafetyManifest,
    ToolCallRecord,
    ToolPolicyManifest,
)
from snp_agent_core.errors import PlatformError


def test_public_imports_are_available() -> None:
    """Public core package imports remain available for apps and packages."""

    assert __version__ == "0.1.0"
    assert AgentManifest.__name__ == "AgentManifest"
    assert AgentRunStatus.COMPLETED.value == "completed"
    assert Citation.__name__ == "Citation"
    assert EvalManifest.__name__ == "EvalManifest"
    assert MemoryManifest.__name__ == "MemoryManifest"
    assert ModelPolicyManifest.__name__ == "ModelPolicyManifest"
    assert ObservabilityManifest.__name__ == "ObservabilityManifest"
    assert RetrievalManifest.__name__ == "RetrievalManifest"
    assert RuntimeContext.__name__ == "RuntimeContext"
    assert RuntimeHealth(status="ok").status == "ok"
    assert RuntimeManifest.__name__ == "RuntimeManifest"
    assert RuntimeRequest.__name__ == "RuntimeRequest"
    assert RuntimeResponse.__name__ == "RuntimeResponse"
    assert SafetyManifest.__name__ == "SafetyManifest"
    assert ToolCallRecord.__name__ == "ToolCallRecord"
    assert ToolPolicyManifest.__name__ == "ToolPolicyManifest"
    assert issubclass(PlatformError, Exception)
