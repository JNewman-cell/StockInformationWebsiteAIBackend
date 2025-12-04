"""
Stock analysis service for AI-powered stock analysis operations.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import json

from app.database.models import ApiUsage, User
from app.agent import StockAgent


class StockAnalysisService:
    """
    Service class for stock analysis operations.
    Coordinates between the AI agent and database tracking.
    """
    
    def __init__(self, db: Session, agent: StockAgent):
        self.db = db
        self.agent = agent
    
    async def analyze_ticker_price_action(
        self, 
        ticker: str, 
        user_id: str,
        additional_context: Optional[str] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze price action for a given ticker using the AI agent.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            user_id: ID of the user making the request
            additional_context: Optional additional context for the analysis
            user_email: Optional email of the user
            user_name: Optional name of the user
            
        Returns:
            Dictionary containing the analysis results
        """
        # Construct the query for the AI agent
        query = f"Summarize the price action for {ticker}"
        if additional_context:
            query += f". Additional context: {additional_context}"
        
        try:
            # Call the AI agent
            analysis = await self.agent.process_query(query)
            
            return {
                "ticker": ticker.upper(),
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Agent error: {type(e).__name__}: {str(e)}")
            raise e
    
    def get_user_usage_stats(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get usage statistics for a user.
        
        Args:
            user_id: User identifier
            limit: Number of recent requests to return
            
        Returns:
            Dictionary with usage statistics
        """
        # Get total request count
        total_requests = self.db.query(ApiUsage).filter(
            ApiUsage.user_id == user_id
        ).count()
        
        # Get recent requests
        recent_requests = self.db.query(ApiUsage).filter(
            ApiUsage.user_id == user_id
        ).order_by(
            ApiUsage.created_at.desc()
        ).limit(limit).all()
        
        return {
            "user_id": user_id,
            "total_requests": total_requests,
            "recent_requests": [
                {
                    "endpoint": req.endpoint,
                    "ticker": req.ticker,
                    "status": req.response_status,
                    "timestamp": req.created_at.isoformat()
                }
                for req in recent_requests
            ]
        }
