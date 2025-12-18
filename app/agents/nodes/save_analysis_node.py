"""
Final node: Save analysis results to database
Saves the generated analysis to the ticker_price_action_analysis table
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.models.ticker_analysis import TickerPriceActionAnalysis


async def save_analysis_node(
    state: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    Final step: Save the analysis result to the database.
    
    This node saves the generated analysis to the ticker_price_action_analysis table.
    Updates existing records or creates new ones using insert/update.
    
    Args:
        state: Current agent state containing response and ticker
        db: Database session
        
    Returns:
        Updated agent state with save status
    """
    # Update progress immediately at start
    state["current_step"] = "saving_analysis"
    state["progress_message"] = "Saving analysis to database"
    
    ticker = state.get("ticker", "").upper()
    analysis_result = state.get("response", "")
    current_step = state.get("current_step", "completed")
    progress_message = state.get("progress_message", "")
    
    if not ticker or not analysis_result:
        state["metadata"]["save_status"] = "Failed - Missing ticker or analysis result"
        return state
    
    try:
        # Try to update existing record
        existing_record = db.query(TickerPriceActionAnalysis).filter(
            TickerPriceActionAnalysis.ticker == ticker
        ).first()
        
        if existing_record:
            existing_record.analysis_result = analysis_result
            existing_record.current_step = current_step
            existing_record.progress_messages = progress_message
            existing_record.status = "completed"
            # Note: updated_at will be automatically updated by server_default=func.now()
            db.merge(existing_record)
        else:
            # Create new record (updated_at will be set automatically)
            new_record = TickerPriceActionAnalysis(
                ticker=ticker,
                analysis_result=analysis_result,
                current_step=current_step,
                progress_messages=progress_message,
                status="completed"
            )
            db.add(new_record)
        
        db.commit()
        state["metadata"]["save_status"] = f"Successfully saved analysis for {ticker}"
        state["progress_message"] = f"Analysis saved successfully for {ticker}"
        state["current_step"] = "completed"
        
    except SQLAlchemyError as e:
        db.rollback()
        state["metadata"]["save_status"] = f"Database error while saving: {str(e)}"
        state["error"] = f"Failed to save analysis: {str(e)}"
    except Exception as e:
        db.rollback()
        state["metadata"]["save_status"] = f"Error saving analysis: {str(e)}"
        state["error"] = f"Failed to save analysis: {str(e)}"
    
    return state
