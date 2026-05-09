"""Production-like mock API package for the customer service agent.

This package provides deterministic, side-effect-free implementations of the
three internal APIs used by the customer service chatbot demo:

- Container tracking API (TMS integration placeholder)
- Booking status API (TMS/booking integration placeholder)
- Support ticket API (CRM/helpdesk integration placeholder)

The mock client and schemas live here so tool execution tests can run without
connecting to any real company systems.  Real adapters will be added behind the
same ``CustomerServiceMockApiClient`` interface in a later PR.

Architecture boundary
---------------------
- This package is agent-specific and lives under ``agents/customer_service/``.
- It imports from ``packages/snp_agent_tools/`` (allowed direction).
- It must never be imported by ``packages/`` or ``apps/``.
- No real HTTP calls, database access, or secrets.
"""
