"""
Utility functions for LLM API calls
"""

import logging
import json
from typing import Dict, Any, Optional, Union
from openai import OpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def call_llm_with_prompt(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
    response_format: Dict[str, str] = {"type": "json_object"}
) -> Any:
    """
    Call OpenAI LLM with system and user prompts
    
    Args:
        system_prompt: System prompt defining the AI's role
        user_prompt: User prompt with the actual task/question
        model: OpenAI model to use (default: gpt-4o)
        temperature: Temperature for response generation (default: 0.3)
        response_format: Response format specification (default: JSON object). 
                        Set to None for plain text responses.
        
    Returns:
        Parsed JSON response from the LLM if response_format is JSON, 
        otherwise plain text string
        
    Raises:
        Exception: If API call fails or response cannot be parsed
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Build request parameters
        request_params = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": temperature
        }
        
        # Only add response_format if it's not None
        if response_format is not None:
            request_params["response_format"] = response_format
        
        response = client.chat.completions.create(**request_params)
        
        content = response.choices[0].message.content
        
        # If response_format is JSON, parse it
        if response_format is not None and response_format.get("type") == "json_object":
            return json.loads(content)
        else:
            # Return plain text
            return content
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response content: {response.choices[0].message.content[:500]}")
        raise
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        raise

