"""Abstract audit sink interface and an in-memory implementation for tests.

A ``ToolCallAuditSink`` is the write target for ``ToolCallAuditRecord`` objects
produced by ``AuditAwareToolExecutor``. The interface is intentionally minimal:
sinks only need to accept and expose records. Filtering, querying, and
aggregation are concerns for higher-level reporting layers.

``InMemoryToolCallAuditSink`` is suitable for unit tests and local development
only. It is not thread-safe and does not persist records across process restarts.
A persistent sink backed by a database or log streaming service will be added in
a later PR once the record contract is stable.
"""

from abc import ABC, abstractmethod

from snp_agent_tools.audit import ToolCallAuditRecord


class ToolCallAuditSink(ABC):
    """Write target for tool call audit records.

    Implementations must accept records in ``record()`` and expose them in
    ``list_records()``. The contract is intentionally simple so that test,
    local, and production sinks can all satisfy it without friction.

    Extension point: future sinks may add async variants, batching, or
    integration with log streaming services. The synchronous interface here
    is the minimal requirement for the current platform layer.
    """

    @abstractmethod
    def record(self, record: ToolCallAuditRecord) -> None:
        """Persist or buffer one tool call audit record.

        Implementations must not raise on valid records. If persistence fails,
        implementations should log the failure and continue rather than
        propagating exceptions to the calling executor, which would interfere
        with tool execution observability.
        """

    @abstractmethod
    def list_records(self) -> list[ToolCallAuditRecord]:
        """Return all audit records held by this sink.

        The returned list should preserve insertion order. Callers must treat
        the returned list as a snapshot; mutations are not guaranteed to be
        reflected in the sink.
        """


class InMemoryToolCallAuditSink(ToolCallAuditSink):
    """In-memory audit sink for unit tests and local development.

    Records are stored in a plain list in insertion order. This sink is not
    thread-safe and does not persist records across process restarts. It is
    intended only for test assertions and local debugging workflows.

    Do not use this sink in production or in any context where audit durability
    or concurrent access is required.
    """

    def __init__(self) -> None:
        """Create an empty in-memory audit sink."""

        self._records: list[ToolCallAuditRecord] = []

    def record(self, record: ToolCallAuditRecord) -> None:
        """Append one audit record to the in-memory list."""

        self._records.append(record)

    def list_records(self) -> list[ToolCallAuditRecord]:
        """Return a shallow copy of all stored records in insertion order."""

        return list(self._records)
