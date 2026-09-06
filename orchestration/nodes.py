from typing import Literal

from .models import OrchestratorState

from sourcing.models import ReplacementRequest
from sourcing.graph import sourcing_graph

'''
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
'''


def tracking_agent_node(state: OrchestratorState):
    """
    Temporary mock for Agent 2
    :param state:
    :return:
    """
    # print("Agent 2: Checking order status")

    request = ReplacementRequest(
        part_number="30112",
        quantity=250,
        unit_price=349.38,
        vendor_name="Meridian Components Pte Ltd."
    )

    return {
        "tracking_status": "DELAYED",
        "replacement_request": request
    }


def sourcing_agent_node(state: OrchestratorState):
    # print("Agent 3: Finding replacement")
    result = sourcing_graph.invoke({
        "request": state["replacement_request"]
    })

    return {
        "replacement_result": result
    }


def route_tracking_result(state: OrchestratorState) -> Literal["supplier_sourcing", "finish"]:
    if state["tracking_status"] in ["DELAYED", "UNAVAILABLE"]:
        return "supplier_sourcing"

    return "finish"
