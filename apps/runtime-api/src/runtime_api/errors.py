"""Runtime API error types and exception handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AgentNotFoundError(Exception):
    """Raised when an agent identifier is not available in the registry."""

    def __init__(self, agent_id: str) -> None:
        """Store the missing agent identifier for structured error responses."""

        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' was not found.")


def agent_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Convert missing-agent errors into a stable HTTP 404 response."""

    if not isinstance(exc, AgentNotFoundError):
        raise exc

    return JSONResponse(
        status_code=404,
        content={
            "detail": {
                "code": "agent_not_found",
                "message": f"Agent '{exc.agent_id}' was not found.",
            }
        },
    )
