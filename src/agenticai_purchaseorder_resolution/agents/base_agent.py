from abc import ABC, abstractmethod
from logging import ERROR, INFO
from typing import List, Dict, Any
from pydantic import BaseModel
from agenticai_purchaseorder_resolution.utils.helpers import basicLogger, read_yaml
from langchain_core.tools import StructuredTool, tool, BaseTool

"""
Defines the base agent class that all agents inherits from, providing a standardized interface 
for tool execution, logging, and error handling. 

AgentConfig class defines the configuration 
schema for the base agents, including agent_id, model_name, temperature, and max_loops.
"""

class AgentConfig(BaseModel):
    agent_id: str
    model_name: str
    temperature: float
    max_tokens: int | None
    reasoning_format: str
    timeout: int | None
    max_loops: int | None
    max_retries: int | None
    

class BaseAgent(ABC):
    def __init__(self, tools: List[BaseTool], config=read_yaml("config/agent_configs.yaml")):
        self.config = config
        self.tools: List[BaseTool] = tools
        self.memory: List[Dict[str, Any]] = []
        self.state = {}
        self.logger = basicLogger("mainLogger")

    # Final method: All agents track execution the exact same way
    def execute_tool(self, tool: BaseTool, arguments: dict) -> Any:
        """
        Execute a tool by name with the provided arguments.

        Args:
            tool (BaseTool): The tool to execute.
            arguments (dict): A dictionary of arguments to pass to the tool.
        
        Returns:
            Any: The result of the tool execution or an error message if the tool fails.
        """
        self.logger.info(f"Executing {tool.name}")
        if tool not in self.tools:
            self.logger.error(f"Tool {tool.name} not found in available tools: {list(t.name for t in self.tools)}")
            return f"Error: Tool {tool.name} not found."
        try:
            return tool.invoke(input = arguments)
        except Exception as e:
            self.logger.error(f"Tool {tool.name} execution failed with error: {str(e)}")
            return self._handle_tool_failure(tool.name, e)

    # Abstract methods: Forced implementation in child classes
    
    @abstractmethod
    def system_prompt(self, suffix: str) -> str:
        """
        Define the agent's identity and boundaries.
        
        Returns:
            str: System prompt for the agent.
        """
        pass     

    @abstractmethod
    def run(self, task: str) -> str:
        """
        Define the core reasoning loop.

        Args:
            task (str): The task to be executed.

        Returns:
            str: The result of the execution.
        """
        pass

    # Private infrastructure helpers
    def _handle_tool_failure(self, tool_name: str, error: Exception) -> str:
        # Standardized error mitigation or graceful fallback
        self.logger.error(f"Tool {tool_name} failed with error: {str(error)}")
        return f"Tool {tool_name} failed: {str(error)}"

    def _logState(self, state: Dict[str, Any]):
        self.memory.append(state)
        self.logger.info(f"State logged: {state}")