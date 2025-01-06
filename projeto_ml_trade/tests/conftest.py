"""
Shared test configuration and fixtures.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import tempfile
import shutil
from datetime import datetime, timedelta

@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data."""
    temp_dir = tmp_path_factory.mktemp("test_data")
    yield temp_dir
    # Cleanup after all tests
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2023-01-01', periods=1000, freq='H')
    base_price = 100
    
    # Generate realistic price movements
    returns = np.random.normal(0, 0.002, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV data
    high_offsets = np.abs(np.random.normal(0, 0.003, len(dates)))
    low_offsets = np.abs(np.random.normal(0, 0.003, len(dates)))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices * (1 + high_offsets),
        'low': prices * (1 - low_offsets),
        'close': prices * (1 + np.random.normal(0, 0.001, len(dates))),
        'volume': np.random.uniform(1000, 5000, len(dates))
    })
    
    # Ensure OHLC relationships are valid
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    return df

@pytest.fixture(scope="session")
def sample_pattern_data():
    """Create sample data with specific patterns for testing."""
    # Create base data
    dates = pd.date_range(start='2023-01-01', periods=200, freq='H')
    prices = []
    
    # Generate a head and shoulders pattern
    for i in range(200):
        if i < 40:  # Left shoulder
            price = 100 + np.sin(i/20.0) * 10
        elif i < 80:  # Head
            price = 110 + np.sin(i/20.0) * 15
        elif i < 120:  # Right shoulder
            price = 100 + np.sin(i/20.0) * 10
        else:  # Trend continuation
            price = 100 - (i-120) * 0.1
        prices.append(price + np.random.normal(0, 1))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'close': prices
    })
    
    # Generate OHLC data around close prices
    df['open'] = df['close'] + np.random.normal(0, 1, len(df))
    df['high'] = df[['open', 'close']].max(axis=1) + np.abs(np.random.normal(0, 0.5, len(df)))
    df['low'] = df[['open', 'close']].min(axis=1) - np.abs(np.random.normal(0, 0.5, len(df)))
    df['volume'] = np.random.uniform(1000, 5000, len(df))
    
    return df

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    old_env = dict(os.environ)
    
    # Set test environment variables
    test_env = {
        'DATASET_DIR': 'test_data/dataset',
        'HISTORICAL_DATA_DIR': 'test_data/historical',
        'ENRICHED_DATASET_DIR': 'test_data/enriched_dataset',
        'ENVIRONMENT': 'test',
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'test_data/test.log',
        'BINANCE_API_KEY': 'test_key',
        'BINANCE_API_SECRET': 'test_secret'
    }
    
    os.environ.update(test_env)
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(old_env)

@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture(scope="function")
def mock_binance_client(mocker):
    """Mock Binance client for testing."""
    mock_client = mocker.patch('utils.binance_client.BinanceClient')
    
    # Mock historical klines data
    def mock_get_klines(*args, **kwargs):
        return sample_ohlcv_data()
    
    mock_client.return_value.get_historical_klines.side_effect = mock_get_klines
    return mock_client

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "pattern: mark test as pattern detection test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers and environment."""
    # Skip slow tests unless explicitly requested
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    # Skip integration tests in CI unless explicitly requested
    if os.getenv('CI') and not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="integration test (CI)")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )
