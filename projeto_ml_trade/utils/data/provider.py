"""
Data provider utilities for handling different data sources.
"""
import os
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DataProvider(ABC):
    """Abstract base class for data providers."""
    
    @abstractmethod
    def get_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Get data for specified parameters.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with data or None if not available
        """
        pass
    
    @abstractmethod
    def get_timeframes(self) -> List[str]:
        """Get list of available timeframes.
        
        Returns:
            List of available timeframes
        """
        pass

class BinanceDataProvider(DataProvider):
    """Data provider for Binance exchange."""
    
    def __init__(self, client):
        """Initialize provider with Binance client.
        
        Args:
            client: Binance client instance
        """
        self.client = client
        self._timeframes = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
    
    def get_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Get data from Binance.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with data or None if not available
        """
        try:
            return self.client.download_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Error getting data from Binance: {str(e)}")
            return None
    
    def get_timeframes(self) -> List[str]:
        """Get list of available timeframes.
        
        Returns:
            List of available timeframes
        """
        return self._timeframes.copy()

class CSVDataProvider(DataProvider):
    """Data provider for CSV files."""
    
    def __init__(self, filepath: str):
        """Initialize provider with file path.
        
        Args:
            filepath: Path to CSV file
        """
        self.filepath = filepath
        self.df = pd.read_csv(filepath)
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df.set_index('timestamp', inplace=True)
    
    def get_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Get data from CSV file.
        
        Args:
            symbol: Trading pair symbol (ignored)
            timeframe: Data timeframe (ignored)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with data or None if not available
        """
        try:
            mask = (
                (self.df.index >= pd.Timestamp(start_date)) &
                (self.df.index <= pd.Timestamp(end_date))
            )
            return self.df[mask].copy()
        except Exception as e:
            logger.error(f"Error getting data from CSV: {str(e)}")
            return None
    
    def get_timeframes(self) -> List[str]:
        """Get list of available timeframes.
        
        Returns:
            Empty list since timeframe is fixed in CSV
        """
        return []

class DataProviderFactory:
    """Factory for creating data providers."""
    
    @staticmethod
    def create_provider(provider_type: str = 'binance', **kwargs) -> Optional[DataProvider]:
        """Create data provider instance.
        
        Args:
            provider_type: Type of provider ('binance' or 'csv')
            **kwargs: Provider-specific arguments
            
        Returns:
            DataProvider instance or None if invalid type
        """
        if provider_type == 'binance':
            from app.utils.binance_client import BinanceClient
            return BinanceDataProvider(BinanceClient())
        elif provider_type == 'csv':
            if 'filepath' not in kwargs:
                raise ValueError("File path required")
            return CSVDataProvider(kwargs['filepath'])
        else:
            logger.error(f"Unknown provider type: {provider_type}")
            return None
