"""Agent run status values shared across runtime boundaries."""

from enum import StrEnum


class AgentRunStatus(StrEnum):
    """Terminal or paused states produced by an agent runtime invocation."""

    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_HUMAN = "requires_human"
    REJECTED_BY_SAFETY = "rejected_by_safety"
