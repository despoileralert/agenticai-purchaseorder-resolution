from langchain.agents import create_agent
from agenticai_purchaseorder_resolution.agents.base_agent import *
from agenticai_purchaseorder_resolution.utils.helpers import *
from dotenv import load_dotenv
load_dotenv()

class InvoiceExtractionAgent(BaseAgent):
    def __init__(self, tools):
        super().__init__(tools)
        self.newconfig = AgentConfig(**self.config["ingestionextractor"])
        self.systemPromptStr = "This is a substitute text"
        self.agent = create_agent(self.newconfig.model_name, tools=self.tools,
                                  system_prompt=self.system_prompt(self.systemPromptStr))
        # self._log_event(f"InvoiceExtractionAgent initialized with config: {config} and tools: {list(self.tools.keys())} 
        # and memory: {self.memory} and system prompt: {self.system_prompt('')}")

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

    def run(self, task: str) -> str:
        # Implement the core reasoning loop for invoice extraction
        # This is a placeholder implementation; actual logic will depend on the specific requirements
        self.logger.info(f"Running task: {task}")

        # Example of executing a tool (assuming 'extract_invoice' is a defined tool)
        result = self.execute_tool("extract_invoice", {"task": task})
        self.logger.info(f"Attempting to execute tool 'extract_invoice' with task: {task}")

        #Log results
        self.logger.info(f"Task result: {result}")
        return result

if __name__ == "__main__":
    # Example usage
    agenttools = [{"tool A": "first_tool", "tool B": "another_tool"}]  # Define your tools here
    agent = InvoiceExtractionAgent(tools=agenttools)
    agent.logger.info(f"System prompt: {agent.system_prompt(agent.systemPromptStr)}")
    task = "Extract invoice details from the provided document."
    result = agent.run(task)