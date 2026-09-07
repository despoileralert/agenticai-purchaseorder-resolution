import operator
from typing import Annotated, Sequence, List, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AnyMessage


# Defining state
class MessagesState(TypedDict):
    messages: Annotated[
        List[BaseMessage], operator.add
    ]  
    # a list of messages shared between agents
    sender: Annotated[str, "The sender of the last message"]
    llm_calls: int


class FulfillmentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
    po_number: str | None
    fulfillment_status: str | None   # written by tool_node
    exception: dict[str, Any] | None # written by flag_exception