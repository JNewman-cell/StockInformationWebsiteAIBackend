"""
StockInformationWebsiteAIBackend - Main Application Module

This is the entry point for the FastAPI application with LangGraph AI agent integration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

from app.agent import StockAgent
from app.config import Settings, get_settings

# Load environment variables
load_dotenv()

# Initialize agent variable
stock_agent: Optional[StockAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    global stock_agent
    settings = get_settings()
    stock_agent = StockAgent(settings)
    print(f"🚀 {settings.app_name} v{settings.app_version} started successfully!")
    yield
    # Shutdown
    print("Shutting down gracefully...")


# Initialize FastAPI app
app = FastAPI(
    title="Stock Information Website AI Backend",
    description="A FastAPI backend with LangGraph AI agent for stock information analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Configure via CORS_ORIGINS environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for AI agent queries"""
    query: str = Field(..., description="User query about stocks")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the query")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What is the current trend for AAPL stock?",
                "context": {"timeframe": "1 week"}
            }
        }
    }


class QueryResponse(BaseModel):
    """Response model for AI agent queries"""
    response: str = Field(..., description="AI agent response")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    app_name: str
    version: str


@app.get("/", response_model=HealthResponse)
async def root(settings: Settings = Depends(get_settings)):
    """Root endpoint - Health check"""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version
    )


@app.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version
    )


@app.post("/query", response_model=QueryResponse)
async def query_agent(
    request: QueryRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Query the AI agent with a question about stocks.
    
    The agent uses LangGraph to process queries and provide intelligent responses.
    """
    if stock_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response = await stock_agent.process_query(
            query=request.query,
            context=request.context
        )
        return QueryResponse(
            response=response["response"],
            metadata=response.get("metadata")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/agent/info")
async def agent_info(settings: Settings = Depends(get_settings)):
    """Get information about the AI agent configuration"""
    return {
        "model": settings.agent_model,
        "temperature": settings.agent_temperature,
        "max_tokens": settings.agent_max_tokens,
        "status": "active" if stock_agent else "not initialized"
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
