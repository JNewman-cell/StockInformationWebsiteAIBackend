"""
API v1 router - consolidates all v1 endpoints.
"""

from fastapi import APIRouter
from .endpoints import analysis, users

api_router = APIRouter(prefix="/api/v1")

# Include endpoint routers
api_router.include_router(analysis.router, tags=["Analysis"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
