"""
User endpoints for user management and statistics.
"""

from fastapi import APIRouter, Depends, status
from typing import Dict, Any
from app.api.middleware.auth import get_current_user

router = APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
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
