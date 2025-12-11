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
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze price action for a ticker through the agent workflow.
        
        The workflow:
        1. Checks if analysis exists and is fresh (from today)
        2. If cached → returns cached result with 200 status
        3. If not cached or stale → runs new analysis and saves to database
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            context: Optional additional context for the analysis
            
        Returns:
            Dict with analysis_result, updated_at, and should_analyze flag
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
            "error": None
        }
        
        # Execute the workflow
        try:
            result = await self.graph.ainvoke(state)
            
            # If cached analysis was used
            if result.get("cached_analysis"):
                return {
                    "analysis_result": result["cached_analysis"]["analysis_result"],
                    "updated_at": result["cached_analysis"]["updated_at"],
                    "from_cache": True,
                    "status_code": 200
                }
            
            # If new analysis was run and saved
            if result.get("response"):
                return {
                    "analysis_result": result["response"],
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
