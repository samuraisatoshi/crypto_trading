"""
Tests for chart components.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.components.backtest.chart_component import (
    create_candlestick_chart,
    update_chart,
    create_trade_chart
)

@pytest.fixture
def sample_data():
    """Create sample OHLCV data."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
    base_price = 100
    
    # Generate realistic price movements
    returns = np.random.normal(0, 0.002, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.normal(0, 0.001, len(dates))),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.002, len(dates)))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.002, len(dates)))),
        'close': prices * (1 + np.random.normal(0, 0.001, len(dates))),
        'volume': np.random.uniform(1000, 5000, len(dates))
    })
    
    # Ensure OHLC relationships
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    return df

@pytest.fixture
def sample_trades():
    """Create sample trade data."""
    return [
        {
            'entry_time': datetime(2023, 1, 1, 12),
            'exit_time': datetime(2023, 1, 1, 16),
            'side': 'long',
            'entry_price': 100.0,
            'exit_price': 105.0,
            'pnl': 5.0,
            'return_pct': 5.0
        },
        {
            'entry_time': datetime(2023, 1, 2, 10),
            'exit_time': datetime(2023, 1, 2, 14),
            'side': 'short',
            'entry_price': 105.0,
            'exit_price': 98.0,
            'pnl': 7.0,
            'return_pct': 6.67
        }
    ]

@pytest.fixture
def sample_patterns():
    """Create sample pattern data."""
    return [
        {
            'type': 'head_and_shoulders',
            'confidence': 0.85,
            'timestamp': datetime(2023, 1, 1, 14),
            'price': 102.0,
            'points': [
                {'timestamp': datetime(2023, 1, 1, 12), 'price': 100.0, 'type': 'shoulder'},
                {'timestamp': datetime(2023, 1, 1, 13), 'price': 103.0, 'type': 'head'},
                {'timestamp': datetime(2023, 1, 1, 14), 'price': 100.0, 'type': 'shoulder'}
            ]
        },
        {
            'type': 'double_bottom',
            'confidence': 0.75,
            'timestamp': datetime(2023, 1, 2, 12),
            'price': 98.0,
            'points': [
                {'timestamp': datetime(2023, 1, 2, 10), 'price': 98.0, 'type': 'bottom'},
                {'timestamp': datetime(2023, 1, 2, 11), 'price': 101.0, 'type': 'peak'},
                {'timestamp': datetime(2023, 1, 2, 12), 'price': 98.0, 'type': 'bottom'}
            ]
        }
    ]

def test_candlestick_chart_creation(sample_data):
    """Test candlestick chart creation."""
    fig = create_candlestick_chart()
    
    # Verify figure properties
    assert fig is not None
    assert fig.layout.xaxis.title.text == 'Time'
    assert fig.layout.yaxis.title.text == 'Price'
    assert fig.layout.dragmode == 'zoom'
    assert fig.layout.showlegend is True

def test_chart_update(sample_data):
    """Test chart updating."""
    fig = create_candlestick_chart()
    
    # Update with initial data
    updated_fig = update_chart(fig, sample_data, 50)
    
    # Verify data update
    assert len(updated_fig.data) > 0
    assert updated_fig.data[0].name == 'Candlesticks'
    
    # Update with more data
    final_fig = update_chart(updated_fig, sample_data, 75)
    assert len(final_fig.data) > 0

def test_trade_chart_creation(sample_data, sample_trades, sample_patterns):
    """Test trade chart creation."""
    results = {
        'trades': sample_trades,
        'patterns': sample_patterns
    }
    
    fig = create_trade_chart(sample_data, results)
    
    # Verify figure properties
    assert fig is not None
    assert fig.layout.xaxis.title.text == 'Time'
    assert fig.layout.yaxis.title.text == 'Price'
    
    # Verify trade markers
    assert any(trace.name == 'Long Entries' for trace in fig.data)
    assert any(trace.name == 'Long Exits' for trace in fig.data)
    assert any(trace.name == 'Short Entries' for trace in fig.data)
    assert any(trace.name == 'Short Exits' for trace in fig.data)
    
    # Verify pattern markers
    assert any('Pattern' in trace.name for trace in fig.data)

def test_chart_data_validation(sample_data):
    """Test chart data validation."""
    # Test with missing columns
    invalid_data = sample_data.drop(['high', 'low'], axis=1)
    with pytest.raises(KeyError):
        create_trade_chart(invalid_data, {'trades': []})
    
    # Test with invalid index
    with pytest.raises(IndexError):
        update_chart(create_candlestick_chart(), sample_data, len(sample_data) + 1)

def test_pattern_visualization(sample_data, sample_patterns):
    """Test pattern visualization."""
    results = {
        'trades': [],
        'patterns': sample_patterns
    }
    
    fig = create_trade_chart(sample_data, results)
    
    # Verify pattern markers
    pattern_traces = [trace for trace in fig.data if 'Pattern' in trace.name]
    assert len(pattern_traces) > 0
    
    # Verify pattern points
    for pattern in sample_patterns:
        pattern_type = pattern['type'].replace('_', ' ').title()
        assert any(pattern_type in trace.name for trace in fig.data)

def test_trade_annotation(sample_data, sample_trades):
    """Test trade annotation."""
    results = {
        'trades': sample_trades,
        'patterns': []
    }
    
    fig = create_trade_chart(sample_data, results)
    
    # Verify trade annotations
    annotations = fig.layout.annotations
    assert any('Long' in ann.text for ann in annotations)
    assert any('Short' in ann.text for ann in annotations)
    assert any('+' in ann.text for ann in annotations)  # Profit markers
    
    # Verify trade lines
    assert any('Entry' in trace.name for trace in fig.data)
    assert any('Exit' in trace.name for trace in fig.data)

def test_chart_update_performance(sample_data):
    """Test chart update performance with large datasets."""
    # Create larger dataset
    large_data = pd.concat([sample_data] * 10, ignore_index=True)
    large_data['timestamp'] = pd.date_range(
        start='2023-01-01',
        periods=len(large_data),
        freq='H'
    )
    
    fig = create_candlestick_chart()
    
    # Test multiple updates
    for i in range(0, len(large_data), 100):
        updated_fig = update_chart(fig, large_data, i)
        assert len(updated_fig.data) > 0
