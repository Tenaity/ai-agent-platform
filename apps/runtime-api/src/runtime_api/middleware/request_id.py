"""X-Request-ID middleware for the runtime API.

Every HTTP request passing through the runtime API receives a stable
``request_id``. The ID is read from the ``X-Request-ID`` header when provided
by the caller (e.g. an API gateway or integration test harness). When absent,
a new UUID4 is generated.

The resolved ``request_id`` is attached to ``request.state`` so downstream
route handlers and the invocation service can read it without coupling to the
HTTP header name. The same ID is echoed back in the ``X-Request-ID`` response
header so callers can correlate their request with platform logs and traces.

Design note: This is implemented as middleware (not a FastAPI dependency)
because middleware executes for every route — including health and version
endpoints — and can set response headers unconditionally. FastAPI dependencies
run per-route and cannot reliably set response headers across all routes.
"""

from __future__ import annotations

import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a stable request identifier to every incoming HTTP request.

    The middleware reads ``X-Request-ID`` from the inbound headers. If the
    header is absent or blank, a new UUID4 string is generated. The resolved
    ID is written to ``request.state.request_id`` and echoed back in the
    ``X-Request-ID`` response header.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Resolve the request ID, attach to state, and propagate in response."""

        inbound = request.headers.get(REQUEST_ID_HEADER, "").strip()
        request_id = inbound if inbound else str(uuid.uuid4())

        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


# Re-export the header name so callers do not hard-code it.
__all__ = ["REQUEST_ID_HEADER", "RequestIdMiddleware"]
