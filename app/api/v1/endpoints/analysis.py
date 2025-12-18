"""
Analysis endpoints for stock price action analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.services import StockAnalysisService
from app.services.stock_analysis_service import TickerNotFoundException
from app.api.middleware.auth import get_current_user
from app.agents.stock_news_analysis_agent import StockAgent

router = APIRouter()


def get_agent_from_request(request: Request) -> Optional[StockAgent]:
    """Get the agent from the request's app state"""
    return getattr(request.app.state, "agent", None)


class PriceActionResponse(BaseModel):
    """Response model for price action analysis."""
    ticker: str
    analysis: Optional[str] = None
    summary: Optional[str] = None
    timestamp: Optional[str] = None
    from_cache: bool = False
    workflow_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status checks."""
    workflow_id: str
    ticker: str
    status: str  # running, completed, failed
    current_step: str
    started_at: str
    completed_at: Optional[str] = None
    progress_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/{ticker}/price-action-analysis", status_code=status.HTTP_200_OK)
async def analyze_price_action(
    ticker: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent: Optional[StockAgent] = Depends(get_agent_from_request)
):
    """
    Analyze the price action of a stock ticker.
    
    This endpoint uses an AI agent to provide insights on price movements,
    trends, and key technical indicators for the specified ticker.
    
    **Returns:**
    - 200 OK with cached analysis: Returns complete analysis from cache (within last 30 minutes)
    - 200 OK with workflow_id: Workflow started, use workflow status endpoint to track progress
    - 404 Not Found: Ticker not found in database
    - 503 Service Unavailable: AI agent not available
    
    **Response Types:**
    - Cached: {"ticker": "AAPL", "analysis": "...", "summary": "...", "from_cache": true}
    - Started: {"ticker": "AAPL", "workflow_id": "uuid", "status": "running", "from_cache": false}
    
    **Authentication Required**: Bearer token must be provided in the
    `x-stack-access-token` header or `Authorization: Bearer <token>` header.
    
    Args:
        ticker: Stock ticker symbol
        current_user: Authenticated user information (injected by middleware)
        db: Database session (injected)
        agent: AI agent instance (injected from app state)
        
    Returns:
        Either cached analysis or workflow_id to track progress
        
    Raises:
        HTTPException: 404 if ticker not found, 503 if agent unavailable
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI agent not available. Please check server configuration."
        )
    
    try:
        service = StockAnalysisService(db=db, agent=agent)
        user_id: str = str(current_user.get("user_id", ""))
        user_email: Optional[str] = current_user.get("email")  # type: ignore[assignment]
        user_name: Optional[str] = current_user.get("username")  # type: ignore[assignment]
        
        result = await service.analyze_ticker_price_action(
            ticker=ticker,
            user_id=user_id,
            additional_context=None
        )
        
        # Return 200 with either cached result or workflow_id
        return PriceActionResponse(**result)
    
    except TickerNotFoundException as e:
        # Return 404 if ticker not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except Exception as e:
        print(f"❌ Error in price action analysis: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze ticker: {str(e)}"
        )


@router.get("/workflow/{workflow_id}/status", response_model=WorkflowStatusResponse, status_code=status.HTTP_200_OK)
async def get_workflow_status(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the current status of a running analysis workflow.
    
    This endpoint is designed to be polled by websockets or frontend clients
    to track the progress of an analysis workflow.
    
    **Workflow States:**
    - running: Workflow is currently executing (check current_step for details)
    - completed: Workflow finished successfully (result field contains analysis)
    - failed: Workflow encountered an error (error field contains details)
    
    **Current Steps:**
    - initializing: Workflow has been created
    - collecting_news: Fetching and analyzing news from sources
    - completed: All steps finished
    - error: Workflow failed
    
    **Usage Pattern:**
    1. Start analysis with POST /{ticker}/price-action-analysis
    2. Receive workflow_id in response
    3. Poll this endpoint with workflow_id to track progress
    4. When status="completed", extract result field for final analysis
    
    Args:
        workflow_id: Unique workflow identifier returned from analysis endpoint
        current_user: Authenticated user information (injected by middleware)
        
    Returns:
        Current workflow status with progress information
        
    Raises:
        HTTPException: 404 if workflow not found
    """
    workflow_status = StockAnalysisService.get_workflow_status(workflow_id)
    
    if not workflow_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found. It may have expired or been cleaned up."
        )
    
    return WorkflowStatusResponse(workflow_id=workflow_id, **workflow_status)
