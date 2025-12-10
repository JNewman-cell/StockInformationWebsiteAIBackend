"""
Ticker price action analysis model for storing AI analysis results.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.base import Base


class TickerPriceActionAnalysis(Base):
    """
    Model for storing ticker price action analysis results.
    
    Stores the AI-generated analysis for each ticker symbol with timestamps.
    Used to determine if fresh analysis is needed or if cached analysis can be returned.
    """
    __tablename__ = "ticker_price_action_analysis"

    ticker = Column(String(7), ForeignKey("ticker_summary.ticker"), primary_key=True, nullable=False, index=True)
    analysis_result = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<TickerPriceActionAnalysis(ticker={self.ticker}, updated_at={self.updated_at})>"
