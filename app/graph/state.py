"""
LangGraph state definitions for the AI agent workflow
"""

from typing import Dict, Any, Optional, Sequence, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(dict):
    """
    State definition for the LangGraph agent.
    
    This TypedDict defines the structure of state passed through the graph:
    - messages: Conversation history (accumulated with operator.add)
    - query: Original user query
    - context: Optional additional context
    - response: Final response to user
    - metadata: Tracking information for debugging/logging
    """
    
    def __init__(self):
        super().__init__()
        self.update({
            "messages": [],
            "query": "",
            "context": None,
            "response": "",
            "metadata": {}
        })


# TypedDict-like structure for type hints
from typing import TypedDict

class AgentStateDict(TypedDict):
    """TypedDict for better IDE support and type checking"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    context: Optional[Dict[str, Any]]
    response: str
    metadata: Dict[str, Any]
