from langchain.agents import create_agent
from langchain.messages import ToolMessage, HumanMessage, AIMessage, SystemMessage
from agenticai_purchaseorder_resolution.agents.base_agent import *
from agenticai_purchaseorder_resolution.utils.helpers import *
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import json
from typing import Dict, Any, AnyStr
from agenticai_purchaseorder_resolution.utils.state import MessagesState
from agenticai_purchaseorder_resolution.utils.tools import extract_invoice


load_dotenv()

class InvoiceExtractionAgent(BaseAgent):
    def __init__(self, tools):
        super().__init__(tools)
        self.newconfig = AgentConfig(**self.config["ingestionextractor"])
        self.systemPromptStr = "Extract line items as a list of dictionaries, vendor id, invoice id, delivery date as a 2-array from when to when, purchase order ID, delivery dates, vendor info which has name and contact email."
        self.agent = create_agent(self.newconfig.model_name, tools=self.tools,
                                  system_prompt=self.system_prompt(self.systemPromptStr))

    def system_prompt(self, suffix: str) -> str:
        return (
            "You are a helpful AI assistant, collaborating with other assistants."
            " Use the provided tools to progress towards answering the question."
            " If you are unable to fully answer, that's OK, another assistant with different tools "
            " will help where you left off. Execute what you can to make progress."
            " If you or any of the other assistants have the final answer or deliverable,"
            " prefix your response with FINAL ANSWER so the team knows to stop."
            f"\n{suffix}"
        )

    def run(self, task: str) -> str | List[str | Dict[Any, Any]]:
        """
        This function takes in a task to extract structured data from an invoice pdf document, 
        and outputs the final results as a json file saved under src/results. 

        Args:
            str task: Instructions for the agent to complete

        Returns:
            dict Result: Structured data extracted from the invoice, written to JSON file. 
        """
        self.logger.info(f"Running task: {task}")

        # Example of executing a tool (assuming 'extract_invoice' is a defined tool)
        # self.execute_tool(extract_invoice, {"task": task})
        self.logger.info(f"Attempting to execute tool 'extract_invoice' with task: {task}")
        question = HumanMessage(content = task)
        response = self.agent.invoke({"messages": [question]})

        #Log toolcalling results
        messages = response.get("messages", [])
        tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
        for msg in tool_messages:
            self.logger.info(f"Tool Call ID: {msg.tool_call_id}")
            self.logger.info(f"Tool Output Content: {msg.content}")
            self.logger.info(f"Tool Artifact: {msg.artifact}") 

        # Writes dictionary output to JSON file for easy reference/usage.
        with open("src/agenticai_purchaseorder_resolution/results/extracted_details.json", "w") as file:
            # Formats the JSON file with 4 spaces of indentation
            json.dump(tool_messages[0].content, file, indent=4)

        return tool_messages[0].content

if __name__ == "__main__":
    # Example usage
    agenttools = [extract_invoice]  # Define your tools here
    agentsys = InvoiceExtractionAgent(tools=agenttools)
    task = "Can you extract structured data from the invoice INV-2026-4100.pdf under the bucket \
            textract-console-ap-southeast-1-56e9d1de-c238-48a1-b770-926a9e7?"
    agentsys.run(task)