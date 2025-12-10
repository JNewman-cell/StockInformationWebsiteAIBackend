"""
API v1 router - consolidates all v1 endpoints.
"""

from fastapi import APIRouter
from .endpoints import analysis

api_router = APIRouter(prefix="/api/v1")

# Include endpoint routers
api_router.include_router(analysis.router, tags=["Analysis"])

