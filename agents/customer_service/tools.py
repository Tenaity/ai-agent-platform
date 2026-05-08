"""Sample customer service tool specifications.

These specs describe capabilities only. PR-009 does not add execution
functions, external integrations, policy enforcement, or credentials.
"""

from snp_agent_tools import ToolExecutionMode, ToolRiskLevel, ToolSpec

tracking_container = ToolSpec(
    name="tracking_container",
    description="Look up container movement milestones by container identifier.",
    risk_level=ToolRiskLevel.LOW,
    execution_mode=ToolExecutionMode.READ,
    input_schema={
        "type": "object",
        "properties": {
            "container_id": {"type": "string"},
        },
        "required": ["container_id"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "container_id": {"type": "string"},
            "status": {"type": "string"},
            "last_event": {"type": "string"},
        },
        "required": ["container_id", "status"],
    },
    required_scopes=["shipment:read"],
    tags=["customer_service", "shipment", "tracking"],
)

check_booking_status = ToolSpec(
    name="check_booking_status",
    description="Read the current status of a shipment booking.",
    risk_level=ToolRiskLevel.LOW,
    execution_mode=ToolExecutionMode.READ,
    input_schema={
        "type": "object",
        "properties": {
            "booking_id": {"type": "string"},
        },
        "required": ["booking_id"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "booking_id": {"type": "string"},
            "status": {"type": "string"},
            "updated_at": {"type": "string"},
        },
        "required": ["booking_id", "status"],
    },
    required_scopes=["booking:read"],
    tags=["customer_service", "booking"],
)

create_support_ticket = ToolSpec(
    name="create_support_ticket",
    description="Create a support ticket for follow-up by the customer service team.",
    risk_level=ToolRiskLevel.MEDIUM,
    execution_mode=ToolExecutionMode.WRITE,
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "subject": {"type": "string"},
            "description": {"type": "string"},
        },
        "required": ["customer_id", "subject", "description"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["ticket_id", "status"],
    },
    required_scopes=["support_ticket:write"],
    approval_required=True,
    tags=["customer_service", "support"],
)

CUSTOMER_SERVICE_TOOL_SPECS = [
    tracking_container,
    check_booking_status,
    create_support_ticket,
]
