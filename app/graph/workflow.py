"""
LangGraph workflow definition and graph construction
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.llm import OpenAIClient
from app.graph.nodes import (
    check_ticker_analysis_node,
    understand_query_node,
    process_query_node,
    generate_response_node,
    save_analysis_node
)


def should_run_analysis(state: Dict[str, Any]) -> str:
    """
    Conditional edge function to determine if analysis should be run.
    
    Args:
        state: Current agent state
        
    Returns:
        "run_analysis" if analysis should be run, "return_cached" otherwise
    """
    return "run_analysis" if state.get("should_analyze", False) else "return_cached"


def create_agent_graph(llm_client: OpenAIClient, db: Session):  # type: ignore[no-untyped-def,return-value]
    """
    Create the LangGraph state graph for ticker price action analysis workflow.
    
    The workflow consists of:
    1. check_ticker: Check if analysis exists and is fresh (today)
       - If cached analysis exists → return_cached (conditional edge)
       - If not → run_analysis (conditional edge)
    2. understand_query: Analyze the analysis request (run_analysis path)
    3. process_query: Generate detailed analysis (run_analysis path)
    4. generate_response: Synthesize final response (run_analysis path)
    5. save_analysis: Save analysis to database (run_analysis path)
    
    Args:
        llm_client: OpenAI client for LLM calls
        db: Database session for ticker analysis lookups
        
    Returns:
        Compiled StateGraph for agent execution
    """
    
    # Create async wrapper functions to properly bind dependencies
    async def check_ticker_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return await check_ticker_analysis_node(state, db)
    
    async def understand_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return await understand_query_node(state, llm_client)
    
    async def process_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return await process_query_node(state, llm_client)
    
    async def generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return await generate_response_node(state, llm_client)
    
    async def save_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return await save_analysis_node(state, db)
    
    workflow = StateGraph(dict)  # type: ignore[arg-type]
    
    # Add the check_ticker node as entry point
    workflow.add_node(
        "check_ticker",
        check_ticker_node  # type: ignore[arg-type]
    )
    
    # Add analysis workflow nodes
    workflow.add_node(
        "understand_query",
        understand_node  # type: ignore[arg-type]
    )
    workflow.add_node(
        "process_query",
        process_node  # type: ignore[arg-type]
    )
    workflow.add_node(
        "generate_response",
        generate_node  # type: ignore[arg-type]
    )
    workflow.add_node(
        "save_analysis",
        save_node  # type: ignore[arg-type]
    )
    
    # Set entry point
    workflow.set_entry_point("check_ticker")
    
    # Conditional edges from check_ticker node
    # If cached analysis exists, return it directly
    workflow.add_conditional_edges(
        "check_ticker",
        should_run_analysis,
        {
            "return_cached": END,  # Return cached analysis
            "run_analysis": "understand_query"  # Run new analysis
        }
    )
    
    # Define the analysis workflow edges
    workflow.add_edge("understand_query", "process_query")
    workflow.add_edge("process_query", "generate_response")
    workflow.add_edge("generate_response", "save_analysis")
    workflow.add_edge("save_analysis", END)
    
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
                "id": "check_ticker",
                "label": "Check Ticker Analysis",
                "description": "Check if fresh analysis exists in database"
            },
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
            },
            {
                "id": "save_analysis",
                "label": "Save Analysis",
                "description": "Save analysis result to database"
            }
        ],
        "edges": [
            {"from": "check_ticker", "to": "understand_query", "condition": "analysis needs update"},
            {"from": "check_ticker", "to": "END", "condition": "cached analysis is fresh"},
            {"from": "understand_query", "to": "process_query"},
            {"from": "process_query", "to": "generate_response"},
            {"from": "generate_response", "to": "save_analysis"},
            {"from": "save_analysis", "to": "END"}
        ],
        "entry_point": "check_ticker"
    }

