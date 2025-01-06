"""
Tests for Binance client functionality.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from utils.binance_client import BinanceClient
from utils.binancedownloader import BinanceDownloader

@pytest.fixture
def mock_binance_client():
    """Create mock Binance client."""
    with patch('binance.Client') as mock_client:
        # Mock successful API connection
        client = mock_client.return_value
        client.get_historical_klines.return_value = [
            [
                1499040000000,      # Open time
                "100.0",            # Open
                "105.0",            # High
                "95.0",             # Low
                "102.0",            # Close
                "1000.0",           # Volume
                1499644799999,      # Close time
                "100000.0",         # Quote asset volume
                100,                # Number of trades
                "500.0",            # Taker buy base asset volume
                "50000.0",          # Taker buy quote asset volume
                "0"                 # Ignore
            ]
        ]
        yield client

@pytest.fixture
def binance_downloader(mock_binance_client):
    """Create BinanceDownloader instance with mocked client."""
    return BinanceDownloader(
        api_key='test_key',
        api_secret='test_secret',
        output_dir='test_data'
    )

class TestBinanceClient:
    """Test suite for Binance client functionality."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        with patch('binance.Client') as mock_client:
            client = BinanceClient(
                api_key='test_key',
                api_secret='test_secret'
            )
            
            assert client is not None
            mock_client.assert_called_once_with('test_key', 'test_secret')
    
    def test_download_historical_data(self, mock_binance_client, binance_downloader):
        """Test historical data download."""
        # Set up test parameters
        symbol = 'BTCUSDT'
        interval = '4h'
        start_date = '2023-01-01'
        end_date = '2023-01-02'
        
        # Download data
        df = binance_downloader.download_historical_data(
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        assert all(col in df.columns for col in required_columns)
        
        # Verify data types
        assert df['timestamp'].dtype == 'datetime64[ns]'
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        assert all(df[col].dtype == np.float64 for col in numeric_columns)
    
    def test_data_validation(self, binance_downloader):
        """Test data validation."""
        # Test invalid symbol
        with pytest.raises(ValueError):
            binance_downloader.download_historical_data(
                symbol='INVALID',
                interval='4h',
                start_date='2023-01-01',
                end_date='2023-01-02'
            )
        
        # Test invalid interval
        with pytest.raises(ValueError):
            binance_downloader.download_historical_data(
                symbol='BTCUSDT',
                interval='invalid',
                start_date='2023-01-01',
                end_date='2023-01-02'
            )
        
        # Test invalid date range
        with pytest.raises(ValueError):
            binance_downloader.download_historical_data(
                symbol='BTCUSDT',
                interval='4h',
                start_date='2023-01-02',  # Start after end
                end_date='2023-01-01'
            )
    
    def test_rate_limiting(self, mock_binance_client, binance_downloader):
        """Test rate limiting handling."""
        # Mock rate limit error
        mock_binance_client.get_historical_klines.side_effect = [
            Exception('APIError(code=-1003): Too many requests'),  # First call fails
            [[1499040000000, "100.0", "105.0", "95.0", "102.0", "1000.0",
              1499644799999, "100000.0", 100, "500.0", "50000.0", "0"]]  # Second call succeeds
        ]
        
        # Download should succeed after retry
        df = binance_downloader.download_historical_data(
            symbol='BTCUSDT',
            interval='4h',
            start_date='2023-01-01',
            end_date='2023-01-02'
        )
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
    
    def test_data_integrity(self, binance_downloader):
        """Test downloaded data integrity."""
        df = binance_downloader.download_historical_data(
            symbol='BTCUSDT',
            interval='4h',
            start_date='2023-01-01',
            end_date='2023-01-02'
        )
        
        # Check price relationships
        assert all(df['high'] >= df['low'])
        assert all(df['high'] >= df['open'])
        assert all(df['high'] >= df['close'])
        assert all(df['low'] <= df['open'])
        assert all(df['low'] <= df['close'])
        
        # Check volume
        assert all(df['volume'] >= 0)
        
        # Check timestamps
        assert df['timestamp'].is_monotonic_increasing
    
    def test_error_handling(self, mock_binance_client, binance_downloader):
        """Test error handling."""
        # Test connection error
        mock_binance_client.get_historical_klines.side_effect = Exception('Connection error')
        
        with pytest.raises(Exception) as exc_info:
            binance_downloader.download_historical_data(
                symbol='BTCUSDT',
                interval='4h',
                start_date='2023-01-01',
                end_date='2023-01-02'
            )
        assert 'Connection error' in str(exc_info.value)
    
    def test_data_format(self, binance_downloader):
        """Test data format options."""
        # Test CSV format
        df_csv = binance_downloader.download_historical_data(
            symbol='BTCUSDT',
            interval='4h',
            start_date='2023-01-01',
            end_date='2023-01-02',
            output_format='csv'
        )
        assert isinstance(df_csv, pd.DataFrame)
        
        # Test JSON format
        df_json = binance_downloader.download_historical_data(
            symbol='BTCUSDT',
            interval='4h',
            start_date='2023-01-01',
            end_date='2023-01-02',
            output_format='json'
        )
        assert isinstance(df_json, pd.DataFrame)
    
    def test_multi_pair_download(self, binance_downloader):
        """Test downloading multiple pairs."""
        symbols = ['BTCUSDT', 'ETHUSDT']
        interval = '4h'
        start_date = '2023-01-01'
        end_date = '2023-01-02'
        
        # Download multiple pairs
        dfs = binance_downloader.download_multiple_pairs(
            symbols=symbols,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
        
        assert isinstance(dfs, dict)
        assert all(symbol in dfs for symbol in symbols)
        assert all(isinstance(df, pd.DataFrame) for df in dfs.values())
        
        # Check data alignment
        timestamps = [set(df['timestamp']) for df in dfs.values()]
        assert all(ts == timestamps[0] for ts in timestamps[1:])
