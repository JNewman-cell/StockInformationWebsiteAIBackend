"""
Stock Information Website AI Backend

Main package initialization exposing key classes and utilities.
"""

from app.agent import StockAgent
from app.config import Settings, get_settings

__version__ = "1.0.0"

__all__ = [
    "StockAgent",
    "Settings",
    "get_settings"
]
