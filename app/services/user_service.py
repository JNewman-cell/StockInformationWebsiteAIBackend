"""
User service for user management and authentication.
"""

from sqlalchemy.orm import Session
from typing import Optional
from app.database.models import User


class UserService:
    """
    Service class for user-related operations.
    Handles user creation, retrieval, and management.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: The user's email address
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user_id: str, email: str, username: Optional[str] = None) -> User:
        """
        Create a new user in the database.
        
        Args:
            user_id: Unique user identifier from auth provider
            email: User's email address
            username: Optional username
            
        Returns:
            Created User object
        """
        user = User(
            id=user_id,
            email=email,
            username=username,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_or_create_user(self, user_id: str, email: str, username: Optional[str] = None) -> User:
        """
        Get existing user or create new one if doesn't exist.
        
        Args:
            user_id: Unique user identifier
            email: User's email address
            username: Optional username
            
        Returns:
            User object
        """
        user = self.get_user_by_id(user_id)
        if not user:
            user = self.create_user(user_id, email, username)
        return user
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user was deactivated, False if not found
        """
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            return True
        return False
