"""
User model for authentication and tracking.
"""

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database.base import Base


class User(Base):
    """
    User model for storing user authentication information.
    Integrates with Neon Auth for JWT token validation.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # User ID from JWT token
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
