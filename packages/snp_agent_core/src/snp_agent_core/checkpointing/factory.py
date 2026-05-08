"""Factory for LangGraph checkpoint saver implementations."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from snp_agent_core.checkpointing.config import CheckpointBackend, CheckpointConfig


def build_checkpointer(config: CheckpointConfig) -> Any | None:
    """Build the configured LangGraph checkpointer.

    ``none`` preserves the current stateless execution path. ``memory`` is an
    in-process LangGraph saver intended for tests and local development only;
    durable backends will be added behind this factory later.
    """

    match config.backend:
        case CheckpointBackend.NONE:
            return None
        case CheckpointBackend.MEMORY:
            return InMemorySaver()
