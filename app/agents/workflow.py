"""
LangGraph workflow definition and graph construction
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agents.openai_client import OpenAIClient
from app.agents.nodes import (
    save_analysis_node,
    collect_news_data_node,
    analyze_significance_node,
    generate_summary_node
)


def create_agent_graph(llm_client: OpenAIClient, db: Session):  # type: ignore[no-untyped-def,return-value]
    """
    Create the LangGraph state graph for ticker news analysis workflow.
    
    The workflow consists of:
    1. collect_news_data: Fetch news from ticker, indices, peers and extract article bodies
    2. analyze_significance: Analyze significance of collected news with LLM
    3. generate_summary: Summarize significant news articles
    4. save_analysis: Save analysis to database
    
    Note: Cache checking is done in the service layer before invoking this workflow.
    
    Args:
        llm_client: OpenAI client for LLM calls
        db: Database session for saving analysis
        
    Returns:
        Compiled StateGraph for agent execution
    """
    
    # Create async wrapper functions to properly bind dependencies
    async def collect_data(state: Dict[str, Any]) -> Dict[str, Any]:
        return await collect_news_data_node(state)
    
    async def analyze_significance(state: Dict[str, Any]) -> Dict[str, Any]:
        return await analyze_significance_node(state)
    
    async def generate_summary(state: Dict[str, Any]) -> Dict[str, Any]:
        return await generate_summary_node(state)
    
    async def save_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return await save_analysis_node(state, db)
    
    workflow = StateGraph(dict)  # type: ignore[arg-type]
    
    # Add workflow nodes
    workflow.add_node(
        "collect_news_data",
        collect_data  # type: ignore[arg-type]
    )
    workflow.add_node(
        "analyze_significance",
        analyze_significance  # type: ignore[arg-type]
    )
    workflow.add_node(
        "generate_summary",
        generate_summary  # type: ignore[arg-type]
    )
    workflow.add_node(
        "save_analysis",
        save_node  # type: ignore[arg-type]
    )
    
    # Set entry point to collect_news_data
    workflow.set_entry_point("collect_news_data")
    
    # Define the linear workflow edges
    workflow.add_edge("collect_news_data", "analyze_significance")
    workflow.add_edge("analyze_significance", "generate_summary")
    workflow.add_edge("generate_summary", "save_analysis")
    workflow.add_edge("save_analysis", END)
    
    # Initialize checkpointer for state persistence between nodes
    checkpointer = MemorySaver()
    
    # Compile and return the graph with checkpointing enabled
    return workflow.compile(checkpointer=checkpointer)


def get_graph_structure() -> Dict[str, Any]:
    """
    Get the structure of the agent's graph for visualization and debugging.
    
    Returns:
        Dict describing the graph structure
    """
    return {
        "nodes": [
            {
                "id": "collect_news_data",
                "label": "Collect News Data",
                "description": "Fetch news from indices, peers, ticker; extract article bodies; fetch prices"
            },
            {
                "id": "analyze_significance",
                "label": "Analyze Significance",
                "description": "Analyze news significance using LLM (batched analysis)"
            },
            {
                "id": "generate_summary",
                "label": "Generate Summary",
                "description": "Summarize significant news articles (>0.5 significance)"
            },
            {
                "id": "save_analysis",
                "label": "Save Analysis",
                "description": "Save analysis result to database"
            }
        ],
        "edges": [
            {"from": "collect_news_data", "to": "analyze_significance"},
            {"from": "analyze_significance", "to": "generate_summary"},
            {"from": "generate_summary", "to": "save_analysis"},
            {"from": "save_analysis", "to": "END"}
        ],
        "entry_point": "collect_news_data",
        "note": "Cache checking is handled in the service layer before invoking this workflow"
    }

