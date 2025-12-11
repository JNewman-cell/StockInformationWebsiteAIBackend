"""
First node: Query Understanding
Analyzes user's query to understand intent and context
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from app.agents.openai_client import OpenAIClient


async def understand_query_node(
    state: Dict[str, Any],
    llm_client: OpenAIClient
) -> Dict[str, Any]:
    """
    First step: Understand the user's query.
    
    This node analyzes the user's query to extract intent, key terms,
    and understand what they're asking about.
    
    Args:
        state: Current agent state
        llm_client: OpenAI client for LLM calls
        
    Returns:
        Updated agent state with understanding metadata
    """
    system_message = SystemMessage(
        content=(
            "You are an expert stock market analyst. "
            "Analyze the user's query to understand their intent and identify key topics. "
            "Respond with a brief analysis of what the user is asking."
        )
    )
    
    human_message = HumanMessage(content=state["query"])
    messages: List[BaseMessage] = [system_message, human_message]
    
    # Call OpenAI API through client
    response = await llm_client.invoke(messages)
    
    # Update state
    state["messages"] = messages + [response]
    state["metadata"]["understanding"] = response.content
    
    return state
