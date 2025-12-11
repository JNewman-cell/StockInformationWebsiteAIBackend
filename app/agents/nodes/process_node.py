"""
Second node: Query Processing
Processes the query with provided context
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from app.agents.openai_client import OpenAIClient


async def process_query_node(
    state: Dict[str, Any],
    llm_client: OpenAIClient
) -> Dict[str, Any]:
    """
    Second step: Process the query with context.
    
    This node takes the analyzed query and any additional context
    to generate detailed analysis and insights.
    
    Args:
        state: Current agent state with previous messages
        llm_client: OpenAI client for LLM calls
        
    Returns:
        Updated agent state with processing results
    """
    context_info = ""
    if state.get("context"):
        context_info = f"\n\nAdditional context: {state['context']}"
    
    processing_message = HumanMessage(
        content=(
            f"Based on the query: '{state['query']}'{context_info}\n\n"
            "Provide a detailed analysis with specific data points and insights."
        )
    )
    
    messages = state["messages"] + [processing_message]
    
    # Call OpenAI API through client
    response = await llm_client.invoke(messages)
    
    # Update state
    state["messages"] = messages + [response]
    state["metadata"]["processing"] = response.content
    
    return state
