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
    - news_data: Collected news articles from ticker, indices, and peers
    - price_action_data: Price movements for ticker, indices, and peers
    - significance_analysis: LLM analysis of price movement significance
    - peers: List of peer ticker symbols
    - news_summary: LLM-generated summary of significant news articles
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
            "error": None,
            "news_data": {},
            "price_action_data": {},
            "significance_analysis": None,
            "all_analyses": {},
            "peers": [],
            "news_summary": None,
            "current_step": "initializing",
            "progress_message": ""
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
    news_data: Dict[str, Any]
    price_action_data: Dict[str, Any]
    significance_analysis: Optional[Dict[str, Any]]
    all_analyses: Dict[str, Dict[str, Any]]
    peers: list[str]
    news_summary: Optional[str]
    current_step: str
    progress_message: str

