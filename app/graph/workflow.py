"""
LangGraph workflow definition and graph construction
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any
from app.llm import OpenAIClient
from app.graph.nodes import (
    understand_query_node,
    process_query_node,
    generate_response_node
)


def create_agent_graph(llm_client: OpenAIClient):
    """
    Create the LangGraph state graph for agent workflow.
    
    The workflow consists of three sequential nodes:
    1. understand_query: Analyze user intent
    2. process_query: Generate detailed analysis
    3. generate_response: Synthesize final response
    
    Args:
        llm_client: OpenAI client for LLM calls
        
    Returns:
        Compiled StateGraph for agent execution
    """
    workflow = StateGraph(dict)
    
    # Add nodes to the graph
    # Each node receives the LLM client for making API calls
    workflow.add_node(
        "understand_query",
        lambda state: understand_query_node(state, llm_client)
    )
    workflow.add_node(
        "process_query",
        lambda state: process_query_node(state, llm_client)
    )
    workflow.add_node(
        "generate_response",
        lambda state: generate_response_node(state, llm_client)
    )
    
    # Define the workflow edges (connections between nodes)
    workflow.set_entry_point("understand_query")
    workflow.add_edge("understand_query", "process_query")
    workflow.add_edge("process_query", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Compile and return the graph
    return workflow.compile()


def get_graph_structure() -> Dict[str, Any]:
    """
    Get the structure of the agent's graph for visualization and debugging.
    
    Returns:
        Dict describing the graph structure
    """
    return {
        "nodes": [
            {
                "id": "understand_query",
                "label": "Query Understanding",
                "description": "Analyze user intent and extract key topics"
            },
            {
                "id": "process_query",
                "label": "Query Processing",
                "description": "Generate detailed analysis with context"
            },
            {
                "id": "generate_response",
                "label": "Response Generation",
                "description": "Synthesize final actionable response"
            }
        ],
        "edges": [
            {"from": "understand_query", "to": "process_query"},
            {"from": "process_query", "to": "generate_response"},
            {"from": "generate_response", "to": "END"}
        ],
        "entry_point": "understand_query"
    }
