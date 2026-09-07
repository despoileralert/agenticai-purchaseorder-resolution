from typing import Any
from langchain_core.messages import HumanMessage
from agenticai_purchaseorder_resolution.agents.workflow_agents import *
from agenticai_purchaseorder_resolution.utils.state import *

# Defining Research Agent Node
def ingestor_node(state):
    invoice_extractor = InvoiceExtractionAgent(tools=[extract_invoice])
    result = invoice_extractor.agent.invoke(state)

    last_message = HumanMessage(
        content=result["messages"][-1].content, name="client", additional_kwargs={"role": "user"}
    )
    return {
        "messages": [last_message],
    }

