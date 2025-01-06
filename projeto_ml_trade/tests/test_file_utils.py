"""
Tests for file utilities.
"""
import pytest
import os
import pandas as pd
from pathlib import Path
from app.utils.file_utils import (
    get_available_files,
    ensure_directory_exists,
    get_standardized_filename,
    parse_filename,
    load_data_file
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory with sample files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create sample files
    files = [
        "BTCUSDT_4h_2023-01-01_2023-12-31_native.csv",
        "finrl_BTC_ETH_BNB_1d_2023-01-01_2023-12-31_finrl.csv",
        "enriched_BTCUSDT_4h_native_20231231_235959.parquet",
        "invalid_file.txt"
    ]
    
    # Create sample data
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='H'),
        'open': [100] * 100,
        'high': [105] * 100,
        'low': [95] * 100,
        'close': [101] * 100,
        'volume': [1000] * 100
    })
    
    for file in files:
        if file.endswith('.csv'):
            df.to_csv(data_dir / file, index=False)
        elif file.endswith('.parquet'):
            df.to_parquet(data_dir / file, index=False)
        else:
            (data_dir / file).touch()
    
    return data_dir

def test_get_available_files(temp_data_dir):
    """Test file listing functionality."""
    # Test CSV files only
    csv_files = get_available_files(temp_data_dir, formats=['.csv'])
    assert len(csv_files) == 2
    assert all(f.endswith('.csv') for f in csv_files)
    
    # Test parquet files only
    parquet_files = get_available_files(temp_data_dir, formats=['.parquet'])
    assert len(parquet_files) == 1
    assert all(f.endswith('.parquet') for f in parquet_files)
    
    # Test multiple formats
    all_files = get_available_files(temp_data_dir, formats=['.csv', '.parquet'])
    assert len(all_files) == 3
    assert any(f.endswith('.csv') for f in all_files)
    assert any(f.endswith('.parquet') for f in all_files)

def test_ensure_directory_exists(tmp_path):
    """Test directory creation."""
    test_dir = tmp_path / "test_dir" / "nested" / "path"
    
    # Directory shouldn't exist initially
    assert not test_dir.exists()
    
    # Create directory
    ensure_directory_exists(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    
    # Should handle existing directory
    ensure_directory_exists(test_dir)
    assert test_dir.exists()

def test_get_standardized_filename():
    """Test filename standardization."""
    # Test native format
    native_filename = get_standardized_filename(
        pair="BTCUSDT",
        timeframe="4h",
        start_date="2023-01-01",
        end_date="2023-12-31",
        format_type="native"
    )
    assert "BTCUSDT_4h_2023-01-01_2023-12-31_native" in native_filename
    
    # Test FinRL format
    finrl_filename = get_standardized_filename(
        pair="BTC_ETH_BNB",
        timeframe="1d",
        start_date="2023-01-01",
        end_date="2023-12-31",
        format_type="finrl"
    )
    assert "finrl_BTC_ETH_BNB_1d_2023-01-01_2023-12-31_finrl" in finrl_filename

def test_parse_filename():
    """Test filename parsing."""
    # Test native format
    native_info = parse_filename("BTCUSDT_4h_2023-01-01_2023-12-31_native.csv")
    assert native_info['symbol'] == 'BTCUSDT'
    assert native_info['timeframe'] == '4h'
    assert native_info['start_date'] == '2023-01-01'
    assert native_info['end_date'] == '2023-12-31'
    assert native_info['format'] == 'native'
    
    # Test FinRL format
    finrl_info = parse_filename("finrl_BTC_ETH_BNB_1d_2023-01-01_2023-12-31_finrl.csv")
    assert finrl_info['symbol'] == 'BTC_ETH_BNB'
    assert finrl_info['timeframe'] == '1d'
    assert finrl_info['start_date'] == '2023-01-01'
    assert finrl_info['end_date'] == '2023-12-31'
    assert finrl_info['format'] == 'finrl'
    
    # Test enriched format
    enriched_info = parse_filename("enriched_BTCUSDT_4h_native_20231231_235959.parquet")
    assert enriched_info['symbol'] == 'BTCUSDT'
    assert enriched_info['timeframe'] == '4h'
    assert enriched_info['format'] == 'native'

def test_load_data_file(temp_data_dir):
    """Test data file loading."""
    # Test CSV loading
    csv_file = temp_data_dir / "BTCUSDT_4h_2023-01-01_2023-12-31_native.csv"
    csv_df = load_data_file(csv_file)
    assert isinstance(csv_df, pd.DataFrame)
    assert 'timestamp' in csv_df.columns
    assert all(col in csv_df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    
    # Test parquet loading
    parquet_file = temp_data_dir / "enriched_BTCUSDT_4h_native_20231231_235959.parquet"
    parquet_df = load_data_file(parquet_file)
    assert isinstance(parquet_df, pd.DataFrame)
    assert 'timestamp' in parquet_df.columns
    assert all(col in parquet_df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    
    # Test invalid file
    with pytest.raises(ValueError):
        load_data_file(temp_data_dir / "invalid_file.txt")

def test_file_naming_consistency():
    """Test consistency between filename generation and parsing."""
    # Generate filename
    filename = get_standardized_filename(
        pair="BTCUSDT",
        timeframe="4h",
        start_date="2023-01-01",
        end_date="2023-12-31",
        format_type="native"
    )
    
    # Parse generated filename
    info = parse_filename(filename)
    
    # Verify consistency
    assert info['symbol'] == 'BTCUSDT'
    assert info['timeframe'] == '4h'
    assert info['start_date'] == '2023-01-01'
    assert info['end_date'] == '2023-12-31'
    assert info['format'] == 'native'
