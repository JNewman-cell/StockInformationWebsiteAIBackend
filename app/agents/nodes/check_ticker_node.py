"""
First node: Check ticker analysis availability
Determines if analysis needs to be run or if cached result can be returned
"""

from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.models.ticker_analysis import TickerPriceActionAnalysis
from app.database.models.ticker_summary import TickerSummary


async def check_ticker_analysis_node(
    state: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    First step: Check if ticker analysis needs to be run.
    
    This node checks if:
    1. Ticker exists in the ticker_summary table
    2. Last analysis was updated today (not yesterday or older)
    
    If ticker doesn't exist, mark for analysis (will fail later with 404).
    If analysis doesn't exist or is stale, mark for analysis.
    Otherwise, return cached result.
    
    Args:
        state: Current agent state containing ticker
        db: Database session
        
    Returns:
        Updated agent state with cached_analysis and should_analyze flags
    """
    ticker = state.get("ticker", "").upper()
    
    if not ticker:
        state["should_analyze"] = True
        state["cached_analysis"] = None
        state["error"] = "No ticker provided"
        return state
    
    try:
        # First check if ticker exists in ticker_summary table
        ticker_summary = db.query(TickerSummary).filter(
            TickerSummary.ticker == ticker
        ).first()
        
        if not ticker_summary:
            # Ticker doesn't exist, mark for analysis (will fail with 404 in service layer)
            state["should_analyze"] = True
            state["cached_analysis"] = None
            state["metadata"]["analysis_check"] = "Ticker not found in ticker_summary table"
            return state
        
        # Ticker exists, now check for analysis
        analysis_record = db.query(TickerPriceActionAnalysis).filter(
            TickerPriceActionAnalysis.ticker == ticker
        ).first()
        
        if not analysis_record:
            # No analysis exists yet, need to run it
            state["should_analyze"] = True
            state["cached_analysis"] = None
            state["metadata"]["analysis_check"] = "No existing analysis found"
            return state
        
        # Check if analysis was updated today
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get the actual datetime value from the SQLAlchemy model
        updated_time_value = analysis_record.updated_at
        if not isinstance(updated_time_value, datetime):
            # If it's a column element, this shouldn't happen after query, but handle it
            state["should_analyze"] = True
            state["cached_analysis"] = None
            state["metadata"]["analysis_check"] = "Could not determine update time"
            return state
        
        # If updated_at is from today, use cached result
        # Make sure updated_time is timezone-aware for comparison
        if updated_time_value.tzinfo is None:
            # If naive datetime, assume UTC
            updated_time_value = updated_time_value.replace(tzinfo=timezone.utc)
        
        # Use explicit comparison that returns bool
        is_fresh = bool(updated_time_value >= today_start)
        if is_fresh:
            state["should_analyze"] = False
            state["cached_analysis"] = {
                "analysis_result": analysis_record.analysis_result,
                "updated_at": analysis_record.updated_at.isoformat()
            }
            state["metadata"]["analysis_check"] = f"Using cached analysis from {analysis_record.updated_at}"
            return state
        
        # Analysis is older than today, need to run new analysis
        state["should_analyze"] = True
        state["cached_analysis"] = None
        state["metadata"]["analysis_check"] = f"Analysis is stale (last updated: {analysis_record.updated_at})"
        return state
        
    except Exception as e:
        # On error, default to running analysis
        state["should_analyze"] = True
        state["cached_analysis"] = None
        state["error"] = f"Database error: {str(e)}"
        state["metadata"]["analysis_check"] = f"Error checking database: {str(e)}"
        return state
