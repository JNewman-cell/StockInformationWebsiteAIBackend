"""
Stock Agent Implementation

This module implements the main Stock Agent that orchestrates the LangGraph workflow
for processing stock-related queries using OpenAI API.
"""

from typing import Dict, Any, Optional
from app.config import Settings
from app.llm import OpenAIClient
from app.graph import create_agent_graph, AgentState
from app.graph.workflow import get_graph_structure


class StockAgent:
    """
    LangGraph-based AI agent for stock information queries.
    
    This agent orchestrates a multi-step workflow for processing stock queries:
    1. Understanding the query intent and context
    2. Processing the query with additional analysis
    3. Generating a clear, actionable response
    
    The agent uses OpenAI's GPT models through LangGraph for workflow management.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the Stock Agent.
        
        Args:
            settings: Application settings containing API keys and configuration
            
        Raises:
            ValueError: If OpenAI API key is not configured
        """
        self.settings = settings
        
        # Initialize OpenAI client (handles all API communication)
        self.llm_client = OpenAIClient(settings)
        
        # Create the LangGraph workflow
        self.graph = create_agent_graph(self.llm_client)
    
    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent workflow.
        
        The query passes through three nodes:
        1. understand_query: Analyzes user intent
        2. process_query: Generates detailed analysis
        3. generate_response: Synthesizes final response
        
        Args:
            query: User's question about stocks
            context: Optional additional context (e.g., {"timeframe": "1 week"})
            
        Returns:
            Dict containing:
                - response: The agent's answer to the query
                - metadata: Processing information (understanding, analysis, etc.)
        """
        # Initialize the agent state
        initial_state: Dict[str, Any] = {
            "messages": [],
            "query": query,
            "context": context,
            "response": "",
            "metadata": {
                "query": query,
                "context": context
            }
        }
        
        # Execute the graph workflow
        final_state = await self.graph.ainvoke(initial_state)
        
        # Return the response and metadata
        return {
            "response": final_state["response"],
            "metadata": final_state["metadata"]
        }
    
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
