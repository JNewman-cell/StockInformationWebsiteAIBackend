"""
Ticker summary model for storing basic ticker information.
"""

from sqlalchemy import Column, String, Integer, BigInteger, Numeric
from app.database.base import Base


class TickerSummary(Base):
    """
    Model for ticker summary information.
    
    Contains basic financial metrics and information for each ticker symbol.
    Used to validate that a ticker exists before performing analysis.
    """
    __tablename__ = "ticker_summary"

    ticker = Column(String(20), primary_key=True, nullable=False, index=True)
    cik = Column(Integer)
    market_cap = Column(BigInteger, nullable=False)
    previous_close = Column(Numeric(15, 2), nullable=False)
    pe_ratio = Column(Numeric(10, 2))
    forward_pe_ratio = Column(Numeric(10, 2))
    dividend_yield = Column(Numeric(5, 2))
    payout_ratio = Column(Numeric(5, 2))
    fifty_day_average = Column(Numeric(10, 2), nullable=False)
    two_hundred_day_average = Column(Numeric(10, 2), nullable=False)
    annual_dividend_growth = Column(Numeric(5, 2))
    five_year_avg_dividend_yield = Column(Numeric(5, 2))
    
    def __repr__(self):
        return f"<TickerSummary(ticker={self.ticker}, market_cap={self.market_cap})>"
