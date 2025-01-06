"""
Tests for the DataEnricher class.
"""
import pytest
import pandas as pd
import numpy as np
from utils.data_enricher import DataEnricher

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
    high_prices = np.random.uniform(95, 105, 100)
    low_prices = np.random.uniform(85, 95, 100)
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(90, 100, 100),
        'high': high_prices,
        'low': low_prices,
        'close': np.random.uniform(90, 100, 100),
        'volume': np.random.uniform(1000, 5000, 100)
    })

@pytest.fixture
def enricher(sample_data):
    """Create DataEnricher instance with sample data."""
    return DataEnricher(sample_data)

class TestDataEnricher:
    """Test suite for DataEnricher class."""
    
    def test_initialization(self, enricher, sample_data):
        """Test DataEnricher initialization."""
        assert enricher.df is not None
        assert len(enricher.df) == len(sample_data)
        assert all(col in enricher.df.columns for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def test_add_all_features(self, enricher):
        """Test adding all technical features."""
        enriched_df = enricher.add_all_features()
        
        # Check basic indicators are added
        expected_indicators = [
            'rsi',
            'macd',
            'macd_signal',
            'macd_hist',
            'sma_20',
            'ema_20',
            'atr'
        ]
        
        for indicator in expected_indicators:
            assert any(col.startswith(indicator) for col in enriched_df.columns), f"Missing indicator: {indicator}"
        
        # Check data integrity
        assert len(enriched_df) == len(enricher.df)
        assert not enriched_df.isnull().all().any(), "Found columns with all null values"
    
    def test_save_enriched_data(self, enricher, tmp_path):
        """Test saving enriched data."""
        # Add features
        enriched_df = enricher.add_all_features()
        
        # Save to temporary directory
        output_path = enricher.save_enriched_data(
            pair='BTCUSDT',
            timeframe='1h',
            source_type='test',
            output_dir=str(tmp_path),
            file_format='csv'
        )
        
        # Verify file exists
        assert output_path.exists(), "Output file not created"
        
        # Load and verify data
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(enriched_df)
        assert all(col in loaded_df.columns for col in enriched_df.columns)
    
    @pytest.mark.parametrize("file_format", ['csv', 'parquet'])
    def test_file_formats(self, enricher, tmp_path, file_format):
        """Test different file formats for saving."""
        enriched_df = enricher.add_all_features()
        
        output_path = enricher.save_enriched_data(
            pair='BTCUSDT',
            timeframe='1h',
            source_type='test',
            output_dir=str(tmp_path),
            file_format=file_format
        )
        
        assert output_path.exists(), f"Output file not created for format: {file_format}"
        
        # Verify file can be loaded
        if file_format == 'csv':
            loaded_df = pd.read_csv(output_path)
        else:  # parquet
            loaded_df = pd.read_parquet(output_path)
        
        assert len(loaded_df) == len(enriched_df)
    
    def test_invalid_data(self):
        """Test handling of invalid input data."""
        # Empty DataFrame
        with pytest.raises(ValueError):
            DataEnricher(pd.DataFrame())
        
        # Missing required columns
        invalid_df = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=10),
            'close': np.random.random(10)  # Missing other required columns
        })
        
        with pytest.raises(ValueError):
            DataEnricher(invalid_df)
    
    def test_data_validation(self, sample_data):
        """Test data validation during enrichment."""
        # Create invalid data
        invalid_data = sample_data.copy()
        invalid_data.loc[0, 'high'] = invalid_data.loc[0, 'low'] - 1  # Invalid price relationship
        
        with pytest.raises(ValueError):
            DataEnricher(invalid_data)
        
        # Test NaN handling
        nan_data = sample_data.copy()
        nan_data.loc[0, 'close'] = np.nan
        
        with pytest.raises(ValueError):
            DataEnricher(nan_data)
