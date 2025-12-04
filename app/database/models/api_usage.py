"""
API usage tracking model.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database.base import Base


class ApiUsage(Base):
    """
    Tracks API usage for rate limiting and analytics.
    """
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    ticker = Column(String, nullable=True, index=True)  # Stock ticker being analyzed
    request_data = Column(Text, nullable=True)  # JSON string of request parameters
    response_status = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<ApiUsage(id={self.id}, user_id={self.user_id}, endpoint={self.endpoint})>"
