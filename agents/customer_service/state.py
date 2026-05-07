"""State schema for the customer service LangGraph sample."""

from typing import TypedDict


class CustomerServiceState(TypedDict):
    """Minimal graph state for the customer service hello runtime."""

    thread_id: str
    tenant_id: str
    user_id: str
    channel: str
    message: str
    final_answer: str | None
