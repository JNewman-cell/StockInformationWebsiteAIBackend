"""
Third node: Response Generation
Generates the final user-facing response
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from app.agents.openai_client import OpenAIClient


async def generate_response_node(
    state: Dict[str, Any],
    llm_client: OpenAIClient
) -> Dict[str, Any]:
    """
    Final step: Generate the final response.
    
    This node synthesizes the analysis into a clear, actionable response
    that directly addresses the user's query.
    
    Args:
        state: Current agent state with full message history
        llm_client: OpenAI client for LLM calls
        
    Returns:
        Updated agent state with final response
    """
    final_message = HumanMessage(
        content=(
            "Summarize your analysis into a clear, concise, actionable response "
            "that directly answers the user's original query. "
            "Keep it professional and data-driven."
        )
    )
    
    messages = state["messages"] + [final_message]
    
    # Call OpenAI API through client
    response = await llm_client.invoke(messages)
    
    # Update state with final response
    state["response"] = response.content
    state["messages"] = messages + [response]
    state["metadata"]["final_response"] = True
    
    return state
