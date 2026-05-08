"""Tests for LangGraph checkpointing configuration and execution config."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from snp_agent_core.checkpointing import (
    CheckpointBackend,
    CheckpointConfig,
    build_checkpointer,
)
from snp_agent_core.config.settings import Settings
from snp_agent_core.contracts import RuntimeRequest
from snp_agent_core.graph import GraphRunner


class RecordingGraph:
    """Fake graph that records the config passed by GraphRunner."""

    def __init__(self) -> None:
        self.config: dict[str, Any] | None = None

    def invoke(
        self,
        input: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.config = config
        return {"final_answer": input["message"]}


def runtime_request() -> RuntimeRequest:
    """Build a minimal runtime request for graph runner tests."""

    return RuntimeRequest(
        tenant_id="tenant_demo",
        channel="api",
        user_id="user_123",
        thread_id="thread_456",
        message="hello",
    )


def test_default_checkpoint_backend_is_none() -> None:
    """Runtime settings default to disabled checkpointing."""

    settings = Settings.model_validate({})

    assert settings.checkpoint_backend == CheckpointBackend.NONE
    assert settings.checkpoint_namespace is None


def test_checkpoint_backend_none_returns_no_checkpointer() -> None:
    """The none backend preserves stateless graph execution."""

    checkpointer = build_checkpointer(
        CheckpointConfig(backend=CheckpointBackend.NONE),
    )

    assert checkpointer is None


def test_memory_checkpoint_backend_builds_successfully() -> None:
    """The memory backend builds a LangGraph in-memory saver."""

    checkpointer = build_checkpointer(
        CheckpointConfig(backend=CheckpointBackend.MEMORY),
    )

    assert isinstance(checkpointer, InMemorySaver)


def test_thread_id_is_passed_into_graph_execution_config() -> None:
    """Checkpointed graph execution uses thread_id as the continuity key."""

    graph = RecordingGraph()
    runner = GraphRunner(graph=graph, checkpointing_enabled=True)

    response = runner.invoke(runtime_request())

    assert response.status == "completed"
    assert graph.config is not None
    assert graph.config["configurable"]["thread_id"] == "thread_456"
