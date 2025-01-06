"""
Binance client for historical data download.
Provides access to Binance API for downloading historical price data with proper error handling
and rate limit management.
"""
import pandas as pd
import time
import logging
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Optional, Dict
from threading import Lock

logger = logging.getLogger(__name__)

class BinanceClient:
    """Client for downloading historical data from Binance."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize client with optional API credentials.
        
        Args:
            api_key: Binance API key (optional for public endpoints)
            api_secret: Binance API secret (optional for public endpoints)
        """
        self.client = Client(api_key, api_secret)
        self._lock = Lock()
        self._last_request_time = 0
        self.MIN_REQUEST_INTERVAL = 0.1  # 100ms between requests
    
    def _handle_rate_limit(self):
        """Implement rate limiting to avoid API restrictions."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - time_since_last)
        self._last_request_time = time.time()

    def download_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        retry_count: int = 3
    ) -> Optional[pd.DataFrame]:
        """Download historical klines data with retry mechanism.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Time interval (e.g., '1m', '5m', '1h')
            start_date: Start date for historical data
            end_date: End date for historical data
            retry_count: Number of retry attempts for failed requests
        
        Returns:
            DataFrame containing historical price data or None if download fails
        """
        for attempt in range(retry_count):
            try:
                self._handle_rate_limit()
                
                # Convert timeframe to interval
                interval = self._get_interval(timeframe)
                
                # Download klines
                klines = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    end_str=end_date.strftime('%Y-%m-%d %H:%M:%S')
                )
            
                if not klines:
                    logger.warning(f"No data available for {symbol} from {start_date} to {end_date}")
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                
                # Convert types
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                                 'quote_volume', 'trades', 'taker_buy_base', 
                                 'taker_buy_quote']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Set index
                df.set_index('timestamp', inplace=True)
                
                # Add symbol and timeframe
                df['symbol'] = symbol
                df['timeframe'] = timeframe
                
                return df
                
            except BinanceAPIException as e:
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s... Error: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to download data after {retry_count} attempts: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error downloading data: {str(e)}")
                raise
    
    def _get_interval(self, timeframe: str) -> str:
        """Convert timeframe to Binance interval."""
        intervals = {
            '1m': Client.KLINE_INTERVAL_1MINUTE,
            '3m': Client.KLINE_INTERVAL_3MINUTE,
            '5m': Client.KLINE_INTERVAL_5MINUTE,
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '30m': Client.KLINE_INTERVAL_30MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR,
            '2h': Client.KLINE_INTERVAL_2HOUR,
            '4h': Client.KLINE_INTERVAL_4HOUR,
            '6h': Client.KLINE_INTERVAL_6HOUR,
            '8h': Client.KLINE_INTERVAL_8HOUR,
            '12h': Client.KLINE_INTERVAL_12HOUR,
            '1d': Client.KLINE_INTERVAL_1DAY,
            '3d': Client.KLINE_INTERVAL_3DAY,
            '1w': Client.KLINE_INTERVAL_1WEEK,
            '1M': Client.KLINE_INTERVAL_1MONTH
        }
        
        if timeframe not in intervals:
            raise ValueError(f"Invalid timeframe: {timeframe}. Available timeframes: {list(intervals.keys())}")
        
        return intervals[timeframe]
