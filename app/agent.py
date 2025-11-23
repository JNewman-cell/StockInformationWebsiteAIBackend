"""
LangGraph AI Agent Implementation

This module implements a LangGraph-based AI agent for processing stock-related queries.
"""

from typing import Dict, Any, Optional, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import operator

from app.config import Settings


class AgentState(TypedDict):
    """State definition for the LangGraph agent"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    context: Optional[Dict[str, Any]]
    response: str
    metadata: Dict[str, Any]


class StockAgent:
    """
    LangGraph-based AI agent for stock information queries.
    
    This agent uses a state graph to process queries through multiple steps:
    1. Understanding the query
    2. Processing with context
    3. Generating a response
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the Stock Agent.
        
        Args:
            settings: Application settings containing API keys and configuration
        """
        self.settings = settings
        self.llm = ChatOpenAI(
            model=settings.agent_model,
            temperature=settings.agent_temperature,
            max_tokens=settings.agent_max_tokens,
            openai_api_key=settings.openai_api_key
        )
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """
        Create the LangGraph state graph for agent workflow.
        
        Returns:
            Compiled StateGraph for agent execution
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("understand_query", self._understand_query)
        workflow.add_node("process_query", self._process_query)
        workflow.add_node("generate_response", self._generate_response)
        
        # Add edges
        workflow.set_entry_point("understand_query")
        workflow.add_edge("understand_query", "process_query")
        workflow.add_edge("process_query", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    async def _understand_query(self, state: AgentState) -> AgentState:
        """
        First step: Understand the user's query.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        system_message = SystemMessage(
            content="You are an expert stock market analyst. Analyze the user's query to understand their intent."
        )
        human_message = HumanMessage(content=state["query"])
        
        messages = [system_message, human_message]
        response = await self.llm.ainvoke(messages)
        
        state["messages"] = messages + [response]
        state["metadata"]["understanding"] = response.content
        
        return state
    
    async def _process_query(self, state: AgentState) -> AgentState:
        """
        Second step: Process the query with context.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        context_info = ""
        if state.get("context"):
            context_info = f"\n\nAdditional context: {state['context']}"
        
        processing_message = HumanMessage(
            content=f"Based on the query: '{state['query']}'{context_info}\n\nProvide a detailed analysis."
        )
        
        messages = state["messages"] + [processing_message]
        response = await self.llm.ainvoke(messages)
        
        state["messages"] = messages + [response]
        state["metadata"]["processing"] = response.content
        
        return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """
        Final step: Generate the final response.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with final response
        """
        final_message = HumanMessage(
            content="Summarize your analysis into a clear, actionable response for the user."
        )
        
        messages = state["messages"] + [final_message]
        response = await self.llm.ainvoke(messages)
        
        state["response"] = response.content
        state["messages"] = messages + [response]
        state["metadata"]["final_response"] = True
        
        return state
    
    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent workflow.
        
        Args:
            query: User's question about stocks
            context: Optional additional context
            
        Returns:
            Dict containing response and metadata
        """
        initial_state: AgentState = {
            "messages": [],
            "query": query,
            "context": context,
            "response": "",
            "metadata": {
                "query": query,
                "context": context
            }
        }
        
        # Execute the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "response": final_state["response"],
            "metadata": final_state["metadata"]
        }
    
    def get_graph_structure(self) -> Dict[str, Any]:
        """
        Get the structure of the agent's graph for debugging/visualization.
        
        Returns:
            Dict describing the graph structure
        """
        return {
            "nodes": ["understand_query", "process_query", "generate_response"],
            "edges": [
                ("understand_query", "process_query"),
                ("process_query", "generate_response"),
                ("generate_response", "END")
            ],
            "entry_point": "understand_query"
        }
