import operator
from typing import Annotated, Sequence, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


# Defining state
class MessagesState(TypedDict):
    messages: Annotated[
        List[BaseMessage], operator.add
    ]  
    # a list of messages shared between agents
    sender: Annotated[str, "The sender of the last message"]
    llm_calls: int
