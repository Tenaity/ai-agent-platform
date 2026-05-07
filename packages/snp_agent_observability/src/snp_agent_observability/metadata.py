"""Trace metadata helpers for platform graph executions."""

from snp_agent_core.contracts import AgentManifest, RuntimeContext


def build_trace_metadata(
    context: RuntimeContext,
    agent_manifest: AgentManifest,
) -> dict[str, str]:
    """Build stable LangSmith metadata for a graph execution.

    Trace metadata is a platform boundary, not a domain feature. Keeping these
    keys centralized gives every agent run the same routing and ownership
    context without requiring domain agents to know about tracing internals.
    """

    return {
        "request_id": context.request_id,
        "tenant_id": context.tenant_id,
        "channel": context.channel,
        "user_id": context.user_id,
        "thread_id": context.thread_id,
        "agent_id": context.agent_id,
        "agent_version": agent_manifest.version,
        "domain": agent_manifest.domain,
    }
