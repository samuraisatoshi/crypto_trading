"""
Base strategy class.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import pandas as pd

class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""
    
    def __init__(self):
        """Initialize strategy."""
        pass
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """Generate trading signals.
        
        Args:
            df: DataFrame with market data
            
        Returns:
            List of signal dictionaries with:
            - type: 'long' or 'short'
            - confidence: signal confidence (0-1)
            - price: signal price
            - pattern: pattern type (optional)
        """
        pass
    
    @abstractmethod
    def should_exit(self, df: pd.DataFrame, current_idx: int, position: Dict) -> bool:
        """Determine if position should be exited.
        
        Args:
            df: DataFrame with market data
            current_idx: Current index in DataFrame
            position: Current position dictionary
            
        Returns:
            True if position should be exited, False otherwise
        """
        pass
    
    def analyze(self, df: pd.DataFrame, current_idx: int) -> tuple:
        """Analyze current market state.
        
        Args:
            df: DataFrame with market data
            current_idx: Current index in DataFrame
            
        Returns:
            Tuple of (signals, patterns)
        """
        return [], []
