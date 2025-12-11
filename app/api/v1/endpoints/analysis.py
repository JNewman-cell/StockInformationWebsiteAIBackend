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
    analysis: str
    timestamp: Optional[str] = None


@router.post("/{ticker}/price-action-analysis", response_model=PriceActionResponse, status_code=status.HTTP_200_OK)
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
        user_id: str = str(current_user.get("user_id", ""))
        user_email: Optional[str] = current_user.get("email")  # type: ignore[assignment]
        user_name: Optional[str] = current_user.get("username")  # type: ignore[assignment]
        
        result = await service.analyze_ticker_price_action(
            ticker=ticker,
            user_id=user_id,
            additional_context=None,
            user_email=user_email,
            user_name=user_name
        )
        
        return PriceActionResponse(**result)
    
    except TickerNotFoundException as e:
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
