"""Errors raised by tool registry primitives."""


class ToolRegistryError(Exception):
    """Base error for in-memory tool registry failures."""


class DuplicateToolError(ToolRegistryError):
    """Raised when registering a tool name that already exists."""


class ToolNotFoundError(ToolRegistryError):
    """Raised when a requested tool name is not registered."""
