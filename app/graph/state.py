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
    - ticker: Stock ticker symbol for analysis
    - should_analyze: Flag indicating if new analysis should be run
    - cached_analysis: Previously cached analysis result
    - context: Optional additional context
    - response: Final response to user
    - metadata: Tracking information for debugging/logging
    - error: Any error messages
    """
    
    def __init__(self):
        super().__init__()
        self.update({
            "messages": [],
            "query": "",
            "ticker": "",
            "should_analyze": False,
            "cached_analysis": None,
            "context": None,
            "response": "",
            "metadata": {},
            "error": None
        })


# TypedDict-like structure for type hints
from typing import TypedDict

class AgentStateDict(TypedDict):
    """TypedDict for better IDE support and type checking"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    ticker: str
    should_analyze: bool
    cached_analysis: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    response: str
    metadata: Dict[str, Any]
    error: Optional[str]

