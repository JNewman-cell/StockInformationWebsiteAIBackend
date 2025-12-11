"""
Stock analysis service for AI-powered stock analysis operations.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.agents.stock_news_analysis_agent import StockAgent
from app.database.models import TickerSummary


class TickerNotFoundException(Exception):
    """Exception raised when a ticker is not found in the database."""
    pass


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
        
        The workflow:
        1. Validates ticker exists in ticker_summary table
        2. Checks if analysis exists and is fresh (from today)
        3. If cached → returns cached result with 200 status
        4. If not cached or stale → runs new analysis and saves to database
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            user_id: ID of the user making the request
            additional_context: Optional additional context for the analysis
            user_email: Optional email of the user
            user_name: Optional name of the user
            
        Returns:
            Dictionary containing the analysis results with ticker, analysis, and timestamp
            
        Raises:
            TickerNotFoundException: If ticker is not found in ticker_summary table
        """
        # Validate ticker exists in the database
        ticker_upper = ticker.upper()
        ticker_exists = self.db.query(TickerSummary).filter(
            TickerSummary.ticker == ticker_upper
        ).first()
        
        if not ticker_exists:
            raise TickerNotFoundException(f"Ticker '{ticker_upper}' not found in database")
        
        try:
            # Call the AI agent's analyze method with database integration
            result = await self.agent.analyze_ticker_price_action(
                ticker=ticker,
                context={"user_id": user_id, "additional_context": additional_context}
            )
            
            # Check for errors
            if result.get("status_code") == 500:
                raise Exception(result.get("error", "Unknown error"))
            
            return {
                "ticker": ticker.upper(),
                "analysis": result.get("analysis_result", ""),
                "timestamp": result.get("updated_at") or None,
                "from_cache": result.get("from_cache", False)
            }
            
        except Exception as e:
            print(f"❌ Agent error: {type(e).__name__}: {str(e)}")
            raise e
