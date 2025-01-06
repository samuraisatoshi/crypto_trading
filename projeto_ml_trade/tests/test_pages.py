"""
Tests for page components.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.pages.download_page import download_page, _handle_native_download, _handle_finrl_download
from app.pages.enrich_page import enrich_page, _handle_enrichment
from app.pages.backtest_page import backtest_page, _run_backtest

@pytest.fixture
def mock_streamlit():
    """Mock streamlit components."""
    with patch('streamlit.header') as mock_header, \
         patch('streamlit.selectbox') as mock_select, \
         patch('streamlit.text_input') as mock_text, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.spinner') as mock_spinner, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.sidebar') as mock_sidebar:
        
        # Configure mock returns
        mock_select.return_value = 'BTCUSDT'
        mock_text.return_value = 'BTCUSDT'
        mock_button.return_value = True
        mock_sidebar.selectbox.return_value = 'patterns'
        
        yield {
            'header': mock_header,
            'select': mock_select,
            'text': mock_text,
            'button': mock_button,
            'spinner': mock_spinner,
            'success': mock_success,
            'error': mock_error,
            'sidebar': mock_sidebar
        }

@pytest.fixture
def sample_data_dir(tmp_path):
    """Create sample data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create sample data
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='H'),
        'open': np.random.uniform(90, 100, 100),
        'high': np.random.uniform(95, 105, 100),
        'low': np.random.uniform(85, 95, 100),
        'close': np.random.uniform(90, 100, 100),
        'volume': np.random.uniform(1000, 5000, 100)
    })
    
    # Save sample files
    df.to_csv(data_dir / "BTCUSDT_4h_2023-01-01_2023-12-31_native.csv", index=False)
    df.to_parquet(data_dir / "enriched_BTCUSDT_4h_native_20231231_235959.parquet")
    
    return data_dir

def test_download_page(mock_streamlit, sample_data_dir):
    """Test download page functionality."""
    with patch('utils.binance_client.BinanceClient') as mock_client:
        # Mock successful download
        mock_client.return_value.get_historical_klines.return_value = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
            'open': [100] * 10,
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [101] * 10,
            'volume': [1000] * 10
        })
        
        # Test page rendering
        download_page(str(sample_data_dir))
        
        # Verify component calls
        mock_streamlit['header'].assert_called_once()
        mock_streamlit['select'].assert_called()
        mock_streamlit['button'].assert_called()
        mock_streamlit['success'].assert_called()

def test_enrich_page(mock_streamlit, sample_data_dir):
    """Test enrich page functionality."""
    with patch('utils.data_enricher.DataEnricher') as mock_enricher:
        # Mock successful enrichment
        mock_instance = mock_enricher.return_value
        mock_instance.add_all_features.return_value = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
            'open': [100] * 10,
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [101] * 10,
            'volume': [1000] * 10,
            'rsi': [50] * 10,
            'macd': [0] * 10
        })
        
        # Test page rendering
        enrich_page(str(sample_data_dir), str(sample_data_dir))
        
        # Verify component calls
        mock_streamlit['header'].assert_called_once()
        mock_streamlit['select'].assert_called()
        mock_streamlit['button'].assert_called()
        mock_streamlit['success'].assert_called()

def test_backtest_page(mock_streamlit, sample_data_dir):
    """Test backtest page functionality."""
    with patch('backtester.backtester.Backtester') as mock_backtester:
        # Mock successful backtest
        mock_instance = mock_backtester.return_value
        mock_instance.run_backtest_generator.return_value = iter([
            ([], []),  # No signals or patterns
            ([{  # One signal
                'type': 'entry',
                'side': 'long',
                'price': 100.0,
                'timestamp': datetime(2023, 1, 1)
            }], [])
        ])
        mock_instance.get_results.return_value = {
            'performance': {
                'total_return': 15.5,
                'max_drawdown': -8.2,
                'win_rate': 65.0
            },
            'trades': []
        }
        
        # Test page rendering
        backtest_page(str(sample_data_dir))
        
        # Verify component calls
        mock_streamlit['header'].assert_called_once()
        mock_streamlit['select'].assert_called()
        mock_streamlit['button'].assert_called()

def test_download_error_handling(mock_streamlit, sample_data_dir):
    """Test error handling in download page."""
    with patch('utils.binance_client.BinanceClient') as mock_client:
        # Test API error
        mock_client.return_value.get_historical_klines.side_effect = Exception("API Error")
        download_page(str(sample_data_dir))
        mock_streamlit['error'].assert_called()
        
        # Test invalid symbol
        mock_streamlit['text'].return_value = ""
        download_page(str(sample_data_dir))
        mock_streamlit['error'].assert_called()

def test_enrich_error_handling(mock_streamlit, sample_data_dir):
    """Test error handling in enrich page."""
    with patch('utils.data_enricher.DataEnricher') as mock_enricher:
        # Test enrichment error
        mock_enricher.return_value.add_all_features.side_effect = Exception("Enrichment Error")
        enrich_page(str(sample_data_dir), str(sample_data_dir))
        mock_streamlit['error'].assert_called()
        
        # Test missing file
        mock_streamlit['select'].return_value = "nonexistent.csv"
        enrich_page(str(sample_data_dir), str(sample_data_dir))
        mock_streamlit['error'].assert_called()

def test_backtest_error_handling(mock_streamlit, sample_data_dir):
    """Test error handling in backtest page."""
    with patch('backtester.backtester.Backtester') as mock_backtester:
        # Test backtest error
        mock_backtester.return_value.run_backtest_generator.side_effect = Exception("Backtest Error")
        backtest_page(str(sample_data_dir))
        mock_streamlit['error'].assert_called()
        
        # Test invalid strategy
        mock_streamlit['sidebar'].selectbox.return_value = "invalid_strategy"
        backtest_page(str(sample_data_dir))
        mock_streamlit['error'].assert_called()

def test_page_interactions(mock_streamlit, sample_data_dir):
    """Test page component interactions."""
    # Test download workflow
    with patch('utils.binance_client.BinanceClient') as mock_client:
        mock_client.return_value.get_historical_klines.return_value = pd.DataFrame()
        download_page(str(sample_data_dir))
        assert mock_streamlit['spinner'].called
        assert mock_streamlit['success'].called or mock_streamlit['error'].called
    
    # Test enrich workflow
    with patch('utils.data_enricher.DataEnricher') as mock_enricher:
        mock_enricher.return_value.add_all_features.return_value = pd.DataFrame()
        enrich_page(str(sample_data_dir), str(sample_data_dir))
        assert mock_streamlit['spinner'].called
        assert mock_streamlit['success'].called or mock_streamlit['error'].called
    
    # Test backtest workflow
    with patch('backtester.backtester.Backtester') as mock_backtester:
        mock_backtester.return_value.run_backtest_generator.return_value = iter([])
        backtest_page(str(sample_data_dir))
        assert mock_streamlit['spinner'].called
