"""
Stock Agent Implementation

This module implements the main Stock Agent that orchestrates the LangGraph workflow
for processing stock-related queries using OpenAI API.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import Settings
from app.agents.openai_client import OpenAIClient
from app.agents import create_agent_graph, AgentState
from app.agents.workflow import get_graph_structure


class StockAgent:
    """
    LangGraph-based AI agent for stock information queries.
    
    This agent orchestrates a multi-step workflow for processing stock queries:
    1. Checking if fresh analysis exists in database
    2. If not, understanding the query intent and context
    3. Processing the query with additional analysis
    4. Generating a clear, actionable response
    5. Saving the analysis to the database
    
    The agent uses OpenAI's GPT models through LangGraph for workflow management.
    """
    
    def __init__(self, settings: Settings, db: Session):
        """
        Initialize the Stock Agent.
        
        Args:
            settings: Application settings containing API keys and configuration
            db: Database session for ticker analysis storage
            
        Raises:
            ValueError: If OpenAI API key is not configured
        """
        self.settings = settings
        self.db = db
        
        # Initialize OpenAI client (handles all API communication)
        self.llm_client = OpenAIClient(settings)
        
        # Create the LangGraph workflow with database access
        self.graph = create_agent_graph(self.llm_client, db)
    
    async def analyze_ticker_price_action(
        self,
        ticker: str,
        context: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Analyze price action for a ticker through the agent workflow.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            context: Optional additional context for the analysis
            workflow_id: Optional workflow ID for progress tracking
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with analysis_result, updated_at, and progress info
        """
        # Initialize state for the graph
        state = {
            "ticker": ticker.upper(),
            "query": f"Provide a comprehensive price action analysis for {ticker}",
            "should_analyze": False,
            "cached_analysis": None,
            "response": "",
            "messages": [],
            "context": context or {},
            "metadata": {},
            "error": None,
            "current_step": "initializing",
            "progress_message": ""
        }
        
        # Execute the workflow (cache is checked in service layer)
        try:
            # Create config with thread_id for checkpointing
            config = {"configurable": {"thread_id": ticker.upper()}}
            
            # Stream through workflow states if callback provided
            if progress_callback and workflow_id:
                final_state = None
                async for event in self.graph.astream(state, config=config):
                    # Extract state from event
                    for node_name, node_state in event.items():
                        if isinstance(node_state, dict):
                            current_step = node_state.get("current_step", "unknown")
                            message = node_state.get("progress_message", "")
                            print(f"📊 Node: {node_name}, Step: {current_step}, Message: {message}")
                            progress_callback(workflow_id, current_step, message)
                            final_state = node_state
                
                # Use final state from streaming
                result = final_state if final_state else state
            else:
                result = await self.graph.ainvoke(state, config=config)
            
            # Workflow always runs new analysis (cache checked in service)
            return {
                "analysis_result": result.get("response", ""),
                "news_summary": result.get("news_summary"),
                "updated_at": result.get("metadata", {}).get("analysis_time"),
                "from_cache": False,
                "status_code": 200
            }
            
            # Error case
            if result.get("error"):
                return {
                    "analysis_result": None,
                    "error": result["error"],
                    "status_code": 500
                }
            
            return {
                "analysis_result": None,
                "error": "Unknown error in workflow",
                "status_code": 500
            }
            
        except Exception as e:
            print(f"❌ Error in ticker analysis workflow: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "analysis_result": None,
                "error": str(e),
                "status_code": 500
            }
    
    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a user query through the agent workflow.
        
        Args:
            query: User's question about stocks
            context: Optional additional context (e.g., {"timeframe": "1 week"})
            
        Returns:
            The agent's response string
        """
        # For now, just use the LLM directly without graph
        from langchain_core.messages import HumanMessage
        
        # Create a simple prompt
        prompt = f"You are a stock market analyst. {query}"
        
        # Call the LLM
        response = await self.llm_client.invoke([HumanMessage(content=prompt)])
        
        return response.content
    
    def get_graph_structure(self) -> Dict[str, Any]:
        """
        Get the structure of the agent's graph for debugging/visualization.
        
        Useful for understanding the workflow and debugging issues.
        
        Returns:
            Dict describing the graph structure with nodes, edges, and metadata
        """
        return get_graph_structure()
    
    def get_llm_info(self) -> Dict[str, Any]:
        """
        Get information about the configured LLM.
        
        Returns:
            Dict containing model name, temperature, and max tokens
        """
        return self.llm_client.get_model_info()
