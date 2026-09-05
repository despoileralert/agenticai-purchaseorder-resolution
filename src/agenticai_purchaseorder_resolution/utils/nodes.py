from typing import Any
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage
from agenticai_purchaseorder_resolution.agents.workflow_agents import InvoiceExtractionAgent

def invoiceExtraction_node(state) -> MessagesState:
    extractorNode = InvoiceExtractionAgent(tools=[])
    result = extractorNode.agent.invoke(state)

    last_message = HumanMessage(
        content=result["messages"][-1].content, name="researcher"
    )
    return {
        "messages": [last_message],
    }
