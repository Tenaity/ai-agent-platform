"""Dynamic graph loader for manifest-declared graph entrypoints."""

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

from snp_agent_core.contracts import AgentManifest
from snp_agent_core.errors import PlatformError
from snp_agent_core.graph.base import GraphRunner, InvokableGraph


class GraphLoadError(PlatformError):
    """Raised when a manifest-declared graph cannot be imported or built."""


def load_graph_runner(
    manifest: AgentManifest,
    *,
    checkpointer: Any | None = None,
    checkpoint_namespace: str | None = None,
) -> GraphRunner:
    """Load a graph from an agent manifest and wrap it in a `GraphRunner`.

    Dynamic graph loading is a framework extension point: manifests declare the
    graph import path, while runtime processes decide when and how to load it.
    This keeps apps thin and lets future registry or release-channel logic swap
    graph implementations without route changes.
    """

    if manifest.runtime.type != "langgraph":
        raise GraphLoadError(f"Unsupported runtime type '{manifest.runtime.type}'.")

    _load_attribute(manifest.runtime.state_schema)
    builder = _load_callable(manifest.runtime.graph)
    graph = builder(checkpointer=checkpointer)
    if not hasattr(graph, "invoke"):
        raise GraphLoadError(
            f"Graph builder '{manifest.runtime.graph}' did not return an invokable graph."
        )
    return GraphRunner(
        graph=_as_invokable_graph(graph),
        checkpointing_enabled=checkpointer is not None,
        checkpoint_namespace=checkpoint_namespace,
    )


def _load_attribute(import_path: str) -> Any:
    """Load an attribute from a `module:attribute` import path."""

    module_name, separator, attribute_name = import_path.partition(":")
    if not module_name or separator != ":" or not attribute_name:
        raise GraphLoadError(
            f"Invalid import path '{import_path}'. Expected 'module:attribute'."
        )

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        raise GraphLoadError(f"Could not import module '{module_name}'.") from exc

    try:
        return getattr(module, attribute_name)
    except AttributeError as exc:
        raise GraphLoadError(f"Module '{module_name}' does not define '{attribute_name}'.") from exc


def _load_callable(import_path: str) -> Callable[..., Any]:
    """Load a callable from a `module:attribute` import path."""

    attribute = _load_attribute(import_path)

    if not callable(attribute):
        raise GraphLoadError(f"Graph import path '{import_path}' is not callable.")
    return cast("Callable[..., Any]", attribute)


def _as_invokable_graph(graph: Any) -> InvokableGraph:
    """Narrow a dynamically loaded graph object to the protocol used by the runner."""

    return cast("InvokableGraph", graph)
