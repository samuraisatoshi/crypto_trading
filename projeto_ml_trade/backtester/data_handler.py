"""
Data handling for backtesting.
"""
from typing import Dict, List, Any
import pandas as pd
from utils.logging_helper import LoggingHelper

class DataHandler:
    """Handles data loading and preprocessing for backtesting."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize data handler.
        
        Args:
            df: DataFrame with OHLCV data
        """
        self.df = df.copy()
        self.current_idx = 0
        
        LoggingHelper.log(f"Initialized DataHandler with {len(df)} candles")
    
    def get_current_data(self) -> pd.DataFrame:
        """Get data up to current index."""
        return self.df.iloc[:self.current_idx + 1]
    
    def get_current_candle(self) -> pd.Series:
        """Get current candle data."""
        return self.df.iloc[self.current_idx]
    
    def advance(self) -> bool:
        """
        Advance to next candle.
        
        Returns:
            bool: True if advanced successfully, False if at end of data
        """
        if self.current_idx < len(self.df) - 1:
            self.current_idx += 1
            return True
        return False
    
    def reset(self):
        """Reset to beginning of data."""
        self.current_idx = 0
    
    def get_lookback_data(self, lookback: int) -> pd.DataFrame:
        """
        Get data for lookback period.
        
        Args:
            lookback: Number of candles to look back
            
        Returns:
            DataFrame with lookback data
        """
        start_idx = max(0, self.current_idx - lookback + 1)
        return self.df.iloc[start_idx:self.current_idx + 1]
    
    def get_data_since(self, timestamp: pd.Timestamp) -> pd.DataFrame:
        """
        Get data since given timestamp.
        
        Args:
            timestamp: Starting timestamp
            
        Returns:
            DataFrame with data since timestamp
        """
        mask = self.df.index >= timestamp
        start_idx = mask.argmax()
        return self.df.iloc[start_idx:self.current_idx + 1]
    
    def get_data_between(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """
        Get data between timestamps.
        
        Args:
            start: Start timestamp
            end: End timestamp
            
        Returns:
            DataFrame with data between timestamps
        """
        mask = (self.df.index >= start) & (self.df.index <= end)
        return self.df[mask]
    
    def get_progress(self) -> float:
        """
        Get progress through data.
        
        Returns:
            float: Progress percentage (0.0 to 1.0)
        """
        return self.current_idx / (len(self.df) - 1)
    
    def get_current_timestamp(self) -> pd.Timestamp:
        """
        Get current timestamp.
        
        Returns:
            Current timestamp
        """
        return self.df.index[self.current_idx]
