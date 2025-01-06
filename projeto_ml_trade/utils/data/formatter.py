"""
Data formatting utilities for standardizing data formats.
"""
import logging
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class DataFormatter:
    """Data formatting and standardization utilities."""
    
    @staticmethod
    def standardize_ohlcv(df: pd.DataFrame, source: str = 'binance') -> pd.DataFrame:
        """Standardize OHLCV data format.
        
        Args:
            df: Input DataFrame
            source: Data source type ('binance', 'csv', etc.)
            
        Returns:
            Standardized DataFrame
        """
        df = df.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif df.index.name == 'timestamp':
            df.index = pd.to_datetime(df.index)
        else:
            raise ValueError("No timestamp column found")
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Convert numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Set timestamp as index if not already
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        
        # Sort index
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        return df
    
    @staticmethod
    def resample_ohlcv(
        df: pd.DataFrame,
        timeframe: str,
        fill_method: str = 'ffill'
    ) -> pd.DataFrame:
        """Resample OHLCV data to new timeframe.
        
        Args:
            df: Input DataFrame
            timeframe: Target timeframe (e.g., '1H', '4H', '1D')
            fill_method: Method to fill missing values
            
        Returns:
            Resampled DataFrame
        """
        # Ensure DataFrame is properly formatted
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be DatetimeIndex")
        
        # Define aggregation functions
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Resample data
        resampled = df.resample(timeframe).agg(agg_dict)
        
        # Fill missing values
        if fill_method:
            resampled.fillna(method=fill_method, inplace=True)
        
        return resampled
    
    @staticmethod
    def add_timeframe_markers(df: pd.DataFrame) -> pd.DataFrame:
        """Add timeframe marker columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with added marker columns
        """
        df = df.copy()
        
        # Add basic time markers
        df['hour'] = df.index.hour
        df['day'] = df.index.day
        df['week'] = df.index.isocalendar().week
        df['month'] = df.index.month
        df['year'] = df.index.year
        df['dayofweek'] = df.index.dayofweek
        
        # Add session markers
        df['session'] = df.apply(
            lambda x: 'asia' if 0 <= x.name.hour < 8
            else 'london' if 8 <= x.name.hour < 16
            else 'ny', axis=1
        )
        
        # Add weekend marker
        df['is_weekend'] = df.index.dayofweek.isin([5, 6]).astype(int)
        
        return df
    
    @staticmethod
    def to_finrl_format(df: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
        """Convert data to FinRL format.
        
        Args:
            df: Input DataFrame
            symbols: List of symbols in the data
            
        Returns:
            DataFrame in FinRL format
        """
        df = df.copy()
        
        # Reset index if timestamp is index
        if isinstance(df.index, pd.DatetimeIndex):
            df.reset_index(inplace=True)
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Add symbol column if not present
        if 'symbol' not in df.columns:
            if len(symbols) != 1:
                raise ValueError("Must provide single symbol when symbol column not present")
            df['symbol'] = symbols[0]
        
        # Rename columns to FinRL format
        column_map = {
            'timestamp': 'date',
            'symbol': 'tic',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }
        df.rename(columns=column_map, inplace=True)
        
        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date and symbol
        df.sort_values(['date', 'tic'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        return df
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> bool:
        """Validate data quality.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check for required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.error("Missing required columns")
                return False
            
            # Check for invalid values
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if df[col].isnull().any():
                    logger.error(f"Found null values in {col}")
                    return False
                if (df[col] <= 0).any():
                    logger.error(f"Found non-positive values in {col}")
                    return False
            
            # Check OHLC relationships
            if not all(df['high'] >= df['low']):
                logger.error("High values must be >= low values")
                return False
            if not all(df['high'] >= df['open']):
                logger.error("High values must be >= open values")
                return False
            if not all(df['high'] >= df['close']):
                logger.error("High values must be >= close values")
                return False
            if not all(df['low'] <= df['open']):
                logger.error("Low values must be <= open values")
                return False
            if not all(df['low'] <= df['close']):
                logger.error("Low values must be <= close values")
                return False
            
            # Check index
            if not isinstance(df.index, pd.DatetimeIndex):
                logger.error("Index must be DatetimeIndex")
                return False
            if df.index.duplicated().any():
                logger.error("Found duplicate timestamps")
                return False
            if not df.index.is_monotonic_increasing:
                logger.error("Index must be monotonically increasing")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return False
