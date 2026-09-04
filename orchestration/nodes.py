from typing import Literal

from .models import OrchestratorState

from sourcing.models import ReplacementRequest
from sourcing.graph import sourcing_graph


def invoice_agent_node(state: OrchestratorState):
    """
    Temporary mock for Agent 1
    :param state:
    :return:
    """
    print("Agent 1: Parsing invoice")
    return {
        "order_item_id": 123
    }


def tracking_agent_node(state: OrchestratorState):
    """
    Temporary mock for Agent 2
    :param state:
    :return:
    """
    print("Agent 2: Checking order status")

    request = ReplacementRequest(
        order_item_id=50,
        part_number="SKF 6205-2RS1",
        description="25mm x 52mm x 15mm Sealed Bearing",
        unit_price=5.00,
        quantity=2,
        currency="SGD",
    )

    return {
        "tracking_status": "UNAVAILABLE",
        "replacement_request": request
    }


def sourcing_agent_node(state: OrchestratorState):
    print("Agent 3: Finding replacement")
    result = sourcing_graph.invoke({
        "request": state["replacement_request"]
    })

    return {
        "replacement_request": result
    }


def route_tracking_result(state: OrchestratorState) -> Literal["supplier_sourcing", "finish"]:
    if state["tracking_status"] == "UNAVAILABLE":
        return "supplier_sourcing"

    return "finish"
