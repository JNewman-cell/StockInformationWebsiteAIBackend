"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Configuration
    app_name: str = "StockInformationWebsiteAIBackend"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: str = "*"  # Comma-separated list of allowed origins
    
    # OpenAI Configuration
    openai_api_key: str = ""
    
    # Database Configuration (Optional)
    database_url: Optional[str] = None
    
    # JWT Authentication Configuration (for validating tokens from frontend)
    neon_auth_issuer_uri: Optional[str] = None
    stack_jwks_url: Optional[str] = None
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "https://api.stack-auth.com"
    
    # Agent Configuration
    agent_model: str = "gpt-4-turbo-preview"
    agent_temperature: float = 0.7
    agent_max_tokens: int = 2000
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
