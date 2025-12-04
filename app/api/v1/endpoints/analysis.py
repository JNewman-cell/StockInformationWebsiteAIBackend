"""
Analysis endpoints for stock price action analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.services import StockAnalysisService
from app.api.middleware.auth import get_current_user
from app.agent import StockAgent

router = APIRouter()


def get_agent_from_request(request: Request) -> Optional[StockAgent]:
    """Get the agent from the request's app state"""
    return getattr(request.app.state, "agent", None)


class PriceActionRequest(BaseModel):
    """Request model for price action analysis."""
    additional_context: Optional[str] = Field(None, description="Additional context for analysis")


class PriceActionResponse(BaseModel):
    """Response model for price action analysis."""
    ticker: str
    analysis: str
    timestamp: str


@router.post("/{ticker}/price-action-analysis", response_model=PriceActionResponse, status_code=status.HTTP_200_OK)
async def analyze_price_action(
    ticker: str,
    request: PriceActionRequest = Body(default=PriceActionRequest()),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent: Optional[StockAgent] = Depends(get_agent_from_request)
):
    """
    Analyze the price action of a stock ticker.
    
    This endpoint uses an AI agent to provide insights on price movements,
    trends, and key technical indicators for the specified ticker.
    
    **Authentication Required**: Bearer token must be provided in the
    `x-stack-access-token` header or `Authorization: Bearer <token>` header.
    
    Args:
        request: Request body containing ticker and optional context
        current_user: Authenticated user information (injected by middleware)
        db: Database session (injected)
        agent: AI agent instance (injected from app state)
        
    Returns:
        Analysis results with ticker, analysis text, and timestamp
        
    Raises:
        HTTPException: 401 if not authenticated, 500 if analysis fails
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI agent not available. Please check server configuration."
        )
    
    try:
        service = StockAnalysisService(db=db, agent=agent)
        result = await service.analyze_ticker_price_action(
            ticker=ticker,
            user_id=current_user["user_id"],
            additional_context=request.additional_context,
            user_email=current_user.get("email"),
            user_name=current_user.get("username")
        )
        
        return PriceActionResponse(**result)
        
    except Exception as e:
        print(f"❌ Error in price action analysis: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze ticker: {str(e)}"
        )
