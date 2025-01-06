"""
UI-specific extension of the core BinanceClient.
Provides environment-aware initialization and UI-focused utilities.
"""
from utils.binance_client import BinanceClient as CoreBinanceClient
import os
import logging
from typing import Dict
import pandas as pd

logger = logging.getLogger(__name__)

class BinanceClient(CoreBinanceClient):
    """UI-specific BinanceClient that handles environment configuration."""
    
    def __init__(self):
        """Initialize client with environment-specific settings."""
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        super().__init__(api_key, api_secret)
        logger.info("Initialized BinanceClient")
            
    def format_klines_for_chart(self, df: pd.DataFrame) -> Dict[str, list]:
        """Format klines data for charting libraries.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with formatted data for charts
        """
        try:
            return {
                'timestamps': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'open': df['open'].tolist(),
                'high': df['high'].tolist(),
                'low': df['low'].tolist(),
                'close': df['close'].tolist(),
                'volume': df['volume'].tolist()
            }
        except Exception as e:
            logger.error(f"Error formatting klines for chart: {str(e)}")
            return {
                'timestamps': [],
                'open': [],
                'high': [],
                'low': [],
                'close': [],
                'volume': []
            }
