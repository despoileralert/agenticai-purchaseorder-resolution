"""Fulfillment Monitoring Agent.

Adapted from the official LangGraph quickstart, Graph API tab:
    https://docs.langchain.com/oss/python/langgraph/quickstart

Role
    Monitors fulfillment status by querying carrier APIs, ERP systems, or
    vendor portals. All connectors here return MOCK data.

Decision logic
    DELIVERED / IN_TRANSIT              -> update central DB
    DELAYED / CANCELLED / OUT_OF_STOCK  -> raise exception flag for the Orchestrator

Run:
    set FULFILLMENT_MODEL=<provider:model-id>
    python fulfillment_agent.py
"""

from __future__ import annotations

import json
import operator
import os
from typing import Any, Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph
from typing_extensions import Annotated, TypedDict
from agenticai_purchaseorder_resolution.utils.state import *
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# 0. Status vocabulary and mock backends
# ---------------------------------------------------------------------------

OK_STATUSES = {"DELIVERED", "IN_TRANSIT"}
EXCEPTION_STATUSES = {"DELAYED", "CANCELLED", "OUT_OF_STOCK"}

# Stands in for FedEx / UPS REST responses.
MOCK_CARRIER_API: dict[str, dict[str, Any]] = {
    "1Z999AA10123456784": {
        "carrier": "UPS",
        "po_number": "PO-4471",
        "status": "IN_TRANSIT",
        "last_scan": "2026-09-05T14:02:00Z",
        "location": "Jurong West Hub, SG",
        "eta": "2026-09-09",
    },
    "794657123456": {
        "carrier": "FEDEX",
        "po_number": "PO-4472",
        "status": "DELIVERED",
        "last_scan": "2026-09-06T09:41:00Z",
        "location": "Dock 3, Tuas Plant",
        "signed_by": "L. TAN",
    },
    "794657999999": {
        "carrier": "FEDEX",
        "po_number": "PO-4480",
        "status": "DELAYED",
        "last_scan": "2026-09-04T22:15:00Z",
        "location": "Memphis Sort Facility",
        "eta": "2026-09-19",
        "reason_code": "WEATHER_HOLD",
    },
}

# Stands in for SAP / NetSuite fulfillment records.
MOCK_ERP: dict[str, dict[str, Any]] = {
    "PO-4471": {
        "system": "SAP",
        "po_number": "PO-4471",
        "status": "IN_TRANSIT",
        "material": "BRG-2200-SS",
        "qty_ordered": 500,
        "qty_received": 0,
        "tracking_number": "1Z999AA10123456784",
    },
    "PO-4472": {
        "system": "SAP",
        "po_number": "PO-4472",
        "status": "DELIVERED",
        "material": "GSKT-118-NBR",
        "qty_ordered": 1200,
        "qty_received": 1200,
        "tracking_number": "794657123456",
    },
    "PO-4480": {
        "system": "NETSUITE",
        "po_number": "PO-4480",
        "status": "DELAYED",
        "material": "SHFT-9040-CR",
        "qty_ordered": 80,
        "qty_received": 0,
        "tracking_number": "794657999999",
    },
    "PO-4491": {
        "system": "NETSUITE",
        "po_number": "PO-4491",
        "status": "OUT_OF_STOCK",
        "material": "VLV-3311-BR",
        "qty_ordered": 40,
        "qty_received": 0,
        "tracking_number": None,
    },
}

# Stands in for the raw vendor emails your parser would receive.
MOCK_VENDOR_INBOX: dict[str, str] = {
    "PO-4480": (
        "Subject: RE: PO-4480 shipment update\n\n"
        "Hi, unfortunately our Memphis line has a weather hold. "
        "Shipment for PO-4480 (80x SHFT-9040-CR) will be delayed by two weeks, "
        "new ETA 19 Sep. Apologies. -- Dana, Meridian Components"
    ),
    "PO-4491": (
        "Subject: PO-4491 stock issue\n\n"
        "We are out of stock on VLV-3311-BR and cannot commit a date. "
        "Please advise whether to cancel. -- Ravi, Keppel Valve Supply"
    ),
}

# Stands in for the central fulfillment DB.
CENTRAL_DB: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# 1. Define tools and model  (quickstart step 1)
# ---------------------------------------------------------------------------


@tool
def get_carrier_tracking(tracking_number: str) -> dict:
    """Query the carrier REST API (FedEx/UPS) for a tracking number.

    Args:
        tracking_number: Carrier tracking number, e.g. "1Z999AA10123456784".
    """
    return MOCK_CARRIER_API.get(
        tracking_number,
        {"tracking_number": tracking_number, "status": "UNKNOWN",
         "error": "tracking number not found"},
    )


@tool
def get_erp_fulfillment(po_number: str) -> dict:
    """Query the ERP (SAP/NetSuite) for the fulfillment record of a purchase order.

    Args:
        po_number: Purchase order number, e.g. "PO-4471".
    """
    return MOCK_ERP.get(
        po_number,
        {"po_number": po_number, "status": "UNKNOWN",
         "error": "no ERP fulfillment record"},
    )


@tool
def parse_vendor_email(po_number: str) -> dict:
    """Fetch and parse the latest vendor email for a purchase order.

    Use this when the ERP or carrier data is stale, missing, or contradictory.

    Args:
        po_number: Purchase order number, e.g. "PO-4480".
    """
    raw = MOCK_VENDOR_INBOX.get(po_number)
    if raw is None:
        return {"po_number": po_number, "found": False}

    # Stand-in for a real parser (LLM extraction, regex, or a vendor schema).
    upper = raw.upper()
    if "OUT OF STOCK" in upper:
        status = "OUT_OF_STOCK"
    elif "CANCEL" in upper and "DELAY" not in upper:
        status = "CANCELLED"
    elif "DELAY" in upper:
        status = "DELAYED"
    else:
        status = "UNKNOWN"

    return {"po_number": po_number, "found": True, "status": status, "raw_email": raw}


tools = [get_carrier_tracking, get_erp_fulfillment, parse_vendor_email]
tools_by_name = {t.name: t for t in tools}

# The quickstart uses init_chat_model("claude-sonnet-4-6", temperature=0).
# Set FULFILLMENT_MODEL to whatever provider:model-id you are using.
model = init_chat_model(model = "openai:gpt-5-mini", temperature=0)
model_with_tools = model.bind_tools(tools)


# ---------------------------------------------------------------------------
# 2. Define state  (quickstart step 2)
# ---------------------------------------------------------------------------


class FulfillmentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
    po_number: str | None
    fulfillment_status: str | None
    exception: dict[str, Any] | None


SYSTEM_PROMPT = """You are a fulfillment monitoring agent for a purchasing team.

Given a purchase order, determine its current fulfillment status using the tools.
Start with the ERP record. If it gives a tracking number, confirm against the
carrier API. If the ERP record is missing, stale, or contradicts the carrier,
check the vendor email.

Valid statuses: DELIVERED, IN_TRANSIT, DELAYED, CANCELLED, OUT_OF_STOCK.

When you have a confirmed status, stop calling tools and reply with one short
sentence stating the status and the evidence you based it on. Do not speculate
beyond what the tools returned."""


# ---------------------------------------------------------------------------
# 3. Model node  (quickstart step 3)
# ---------------------------------------------------------------------------


def llm_call(state: FulfillmentState):
    """LLM decides which fulfillment source to query, or that it has enough."""
    return {
        "messages": [
            model_with_tools.invoke(
                [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ---------------------------------------------------------------------------
# 4. Tool node  (quickstart step 4, plus status extraction)
# ---------------------------------------------------------------------------


def tool_node(state: FulfillmentState):
    """Run the connector calls and lift any reported status into state.

    The status is taken from the tool's structured return value, not from the
    model's prose, so routing stays deterministic.
    """
    result: list[ToolMessage] = []
    status = state.get("fulfillment_status")
    po_number = state.get("po_number")

    for tool_call in state["messages"][-1].tool_calls:
        selected = tools_by_name[tool_call["name"]]
        observation = selected.invoke(tool_call["args"])

        if isinstance(observation, dict):
            if observation.get("status") and observation["status"] != "UNKNOWN":
                status = observation["status"]
            if observation.get("po_number"):
                po_number = observation["po_number"]

        result.append(
            ToolMessage(
                content=json.dumps(observation),
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": result, "fulfillment_status": status, "po_number": po_number}


# ---------------------------------------------------------------------------
# 5. Routing + terminal nodes  (quickstart step 5, extended)
# ---------------------------------------------------------------------------


def should_continue(
    state: FulfillmentState,
) -> Literal["tool_node", "update_central_db", "flag_exception"]:
    """Loop while the model is still gathering; then branch on the status.

    Anything that is not explicitly a healthy status -- including UNKNOWN or no
    data at all -- is treated as an exception. Fail toward the human.
    """
    if state["messages"][-1].tool_calls:
        return "tool_node"
    if state.get("fulfillment_status") in OK_STATUSES:
        return "update_central_db"
    return "flag_exception"


def update_central_db(state: FulfillmentState):
    """Happy path: DELIVERED / IN_TRANSIT are written to the central DB."""
    po_number = state.get("po_number") or "UNKNOWN_PO"
    record = {
        "po_number": po_number,
        "status": state["fulfillment_status"],
        "source": "fulfillment_monitor",
        "llm_calls": state.get("llm_calls", 0),
    }
    CENTRAL_DB[po_number] = record
    return {
        "messages": [
            HumanMessage(content=f"[central_db] upserted {json.dumps(record)}")
        ],
        "exception": None,
    }


def flag_exception(state: FulfillmentState):
    """Exception path: build the payload the Orchestrator will act on."""
    status = state.get("fulfillment_status") or "UNKNOWN"
    exception = {
        "po_number": state.get("po_number") or "UNKNOWN_PO",
        "status": status,
        "severity": "HIGH" if status in {"CANCELLED", "OUT_OF_STOCK"} else "MEDIUM",
        "requires_human_approval": True,
        "recommended_next_agent": (
            "alternate_sourcing" if status in EXCEPTION_STATUSES else "triage"
        ),
        "evidence": [
            m.content for m in state["messages"] if isinstance(m, ToolMessage)
        ],
    }
    return {
        "messages": [
            HumanMessage(content=f"[exception] {json.dumps(exception)}")
        ],
        "exception": exception,
    }


# ---------------------------------------------------------------------------
# 6. Build and compile  (quickstart step 6)
# ---------------------------------------------------------------------------

agent_builder = StateGraph(FulfillmentState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("update_central_db", update_central_db)
agent_builder.add_node("flag_exception", flag_exception)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", "update_central_db", "flag_exception"],
)
agent_builder.add_edge("tool_node", "llm_call")
agent_builder.add_edge("update_central_db", END)
agent_builder.add_edge("flag_exception", END)

fulfillment_agent = agent_builder.compile(name="fulfillment_monitor")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for po in ["PO-4472", "PO-4480", "PO-4491"]:
        print("=" * 70)
        print(f"Monitoring {po}")
        print("=" * 70)

        final = fulfillment_agent.invoke(
            {
                "messages": [
                    HumanMessage(content=f"What is the fulfillment status of {po}?")
                ],
                "po_number": po,
                "llm_calls": 0,
                "fulfillment_status": None,
                "exception": None,
            }
        )

        for m in final["messages"]:
            m.pretty_print()

        print(f"\nstatus:    {final['fulfillment_status']}")
        print(f"exception: {json.dumps(final['exception'], indent=2)}")
        print()

    print("CENTRAL_DB:", json.dumps(CENTRAL_DB, indent=2))