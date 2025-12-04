"""
OpenAI LLM client wrapper for centralized API communication management
"""

from langchain_openai import ChatOpenAI
from typing import Optional, Dict, Any
from app.config import Settings


class OpenAIClient:
    """
    Wrapper for OpenAI ChatGPT LLM client.
    
    This class centralizes all OpenAI API communication, making it easy to:
    - Switch models
    - Adjust parameters
    - Add logging/monitoring
    - Handle errors consistently
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize OpenAI client with application settings.
        
        Args:
            settings: Application settings containing OpenAI configuration
        """
        self.settings = settings
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> ChatOpenAI:
        """
        Initialize the ChatOpenAI client with configured parameters.
        
        Returns:
            Configured ChatOpenAI instance
            
        Raises:
            ValueError: If API key is not configured
        """
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is not configured")
        
        return ChatOpenAI(
            model=self.settings.agent_model,
            temperature=self.settings.agent_temperature,
            max_tokens=self.settings.agent_max_tokens,
            openai_api_key=self.settings.openai_api_key
        )
    
    async def invoke(self, messages: list) -> Any:
        """
        Invoke the LLM with messages.
        
        Args:
            messages: List of messages to process
            
        Returns:
            LLM response
        """
        return await self.client.ainvoke(messages)
    
    def get_client(self) -> ChatOpenAI:
        """Get the underlying ChatOpenAI client"""
        return self.client
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model"""
        return {
            "model": self.settings.agent_model,
            "temperature": self.settings.agent_temperature,
            "max_tokens": self.settings.agent_max_tokens
        }
