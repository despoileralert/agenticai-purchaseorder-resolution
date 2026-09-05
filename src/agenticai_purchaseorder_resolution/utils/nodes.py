from typing import Any
from langchain_core.messages import HumanMessage
from agenticai_purchaseorder_resolution.agents.workflow_agents import *
from langgraph.graph import MessagesState
from langchain.agents.middleware import InputAgentState


research_agent_system_prompt = """
You can only do research. You are working with a chart generator colleague.
"""

# Defining Research Agent Node
def ingestor_node(state: InputAgentState) -> MessagesState:
    invoice_extractor = InvoiceExtractionAgent(tools=[extract_invoice])
    result = invoice_extractor.agent.invoke(state)

    last_message = HumanMessage(
        content=result["messages"][-1].content, name="client", additional_kwargs={"role": "user"}
    )
    return {
        "messages": [last_message],
    }