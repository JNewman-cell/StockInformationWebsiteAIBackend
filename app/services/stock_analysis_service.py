"""
Stock analysis service for AI-powered stock analysis operations.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from app.agents.stock_news_analysis_agent import StockAgent
from app.database.models import TickerSummary, TickerPriceActionAnalysis


class TickerNotFoundException(Exception):
    """Exception raised when a ticker is not found in the database."""
    pass


# Thread pool for running workflows without blocking event loop
_workflow_executor = ThreadPoolExecutor(max_workers=5)


class StockAnalysisService:
    """
    Service class for stock analysis operations.
    Coordinates between the AI agent and database tracking.
    """
    
    # Class-level storage for running workflows
    _running_workflows: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, db: Session, agent: StockAgent):
        self.db = db
        self.agent = agent
    
    async def analyze_ticker_price_action(
        self, 
        ticker: str, 
        user_id: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze price action for a given ticker using the AI agent.
        
        The workflow:
        1. Validates ticker exists in ticker_summary table
        2. Checks if analysis exists and is fresh (within last 30 minutes)
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
        
        # Check for cached analysis from last 30 minutes
        analysis_record = self.db.query(TickerPriceActionAnalysis).filter(
            TickerPriceActionAnalysis.ticker == ticker_upper
        ).first()
        
        if analysis_record:
            # Check if analysis was updated within last 30 minutes
            now = datetime.now(timezone.utc)
            thirty_minutes_ago = now - timedelta(minutes=30)
            
            updated_time = analysis_record.updated_at
            if updated_time.tzinfo is None:
                updated_time = updated_time.replace(tzinfo=timezone.utc)
            
            # If analysis is from last 30 minutes, return cached result
            if updated_time >= thirty_minutes_ago:
                return {
                    "ticker": ticker_upper,
                    "analysis": analysis_record.analysis_result,
                    "summary": analysis_record.news_summary,
                    "timestamp": analysis_record.updated_at.isoformat(),
                    "from_cache": True
                }
        
        # No cached analysis or stale, start new workflow in background
        workflow_id = str(uuid.uuid4())
        
        # Store workflow metadata
        StockAnalysisService._running_workflows[workflow_id] = {
            "ticker": ticker_upper,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "current_step": "initializing",
            "progress_message": "Workflow starting...",
            "result": None,
            "error": None
        }
        
        # Start workflow in background in a way that doesn't block the event loop
        # Create a new task but don't await it - let it run completely independently
        task = asyncio.create_task(self._run_workflow_background(workflow_id, ticker, user_id, additional_context))
        # Don't store or await the task - just let it run
        
        return {
            "ticker": ticker_upper,
            "workflow_id": workflow_id,
            "status": "running",
            "message": "Analysis workflow started",
            "from_cache": False
        }
    
    async def _run_workflow_background(
        self,
        workflow_id: str,
        ticker: str,
        user_id: str,
        additional_context: Optional[str] = None
    ) -> None:
        """
        Run the analysis workflow in the background and update status.
        Updates progress from checkpoint state.
        
        Args:
            workflow_id: Unique workflow identifier
            ticker: Stock ticker symbol
            user_id: User ID requesting the analysis
            additional_context: Optional additional context
        """
        try:
            # Get the graph from agent to access checkpointer
            config = {"configurable": {"thread_id": ticker.upper()}}
            
            print(f"🚀 Starting workflow {workflow_id} for {ticker}")
            
            # Call the AI agent's analyze method
            result = await self.agent.analyze_ticker_price_action(
                ticker=ticker,
                context={"user_id": user_id, "additional_context": additional_context},
                workflow_id=workflow_id,
                progress_callback=self._update_workflow_progress
            )
            
            print(f"✅ Workflow {workflow_id} completed. Result keys: {result.keys()}")
            
            # Check for errors
            if result.get("status_code") == 500:
                raise Exception(result.get("error", "Unknown error"))
            
            # Update workflow with final result
            StockAnalysisService._running_workflows[workflow_id].update({
                "status": "completed",
                "current_step": "completed",
                "result": {
                    "ticker": ticker.upper(),
                    "analysis": result.get("analysis_result", ""),
                    "summary": result.get("news_summary"),
                    "timestamp": result.get("updated_at") or None
                },
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            
            print(f"✅ Workflow {workflow_id} status updated to completed")
            
        except Exception as e:
            # Update workflow with error
            StockAnalysisService._running_workflows[workflow_id].update({
                "status": "failed",
                "current_step": "error",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            print(f"❌ Workflow {workflow_id} error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _update_workflow_progress(self, workflow_id: str, current_step: str, message: str):
        """
        Callback to update workflow progress from agent
        
        Args:
            workflow_id: Workflow identifier
            current_step: Current step name
            message: Current progress message
        """
        if workflow_id in StockAnalysisService._running_workflows:
            StockAnalysisService._running_workflows[workflow_id].update({
                "current_step": current_step,
                "progress_message": message
            })
    
    @staticmethod
    def get_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a running workflow.
        
        Args:
            workflow_id: Unique workflow identifier
            
        Returns:
            Dictionary with workflow status, or None if workflow not found
        """
        return StockAnalysisService._running_workflows.get(workflow_id)
    
    @staticmethod
    def cleanup_workflow(workflow_id: str) -> bool:
        """
        Remove a completed workflow from memory.
        
        Args:
            workflow_id: Unique workflow identifier
            
        Returns:
            True if workflow was removed, False if not found
        """
        if workflow_id in StockAnalysisService._running_workflows:
            del StockAnalysisService._running_workflows[workflow_id]
            return True
        return False
