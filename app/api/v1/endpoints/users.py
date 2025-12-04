"""
User endpoints for user management and statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any

from app.database import get_db
from app.services import StockAnalysisService
from app.api.middleware.auth import get_current_user

router = APIRouter()


class UserStatsResponse(BaseModel):
    """Response model for user statistics."""
    user_id: str
    total_requests: int
    recent_requests: List[Dict[str, Any]]


@router.get("/me/stats", response_model=UserStatsResponse, status_code=status.HTTP_200_OK)
async def get_my_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for the authenticated user.
    
    Returns total request count and recent request history.
    
    **Authentication Required**: Bearer token must be provided.
    
    Args:
        current_user: Authenticated user information (injected)
        db: Database session (injected)
        
    Returns:
        User statistics including total and recent requests
    """
    try:
        # Create a temporary agent reference (not used for stats)
        service = StockAnalysisService(db=db, agent=None)
        stats = service.get_user_usage_stats(
            user_id=current_user["user_id"],
            limit=10
        )
        
        return UserStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user stats: {str(e)}"
        )


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Get information about the authenticated user.
    
    **Authentication Required**: Bearer token must be provided.
    
    Args:
        current_user: Authenticated user information (injected)
        
    Returns:
        User information from the JWT token
    """
    return {
        "user_id": current_user["user_id"],
        "email": current_user.get("email"),
        "username": current_user.get("username")
    }
