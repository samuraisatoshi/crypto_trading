"""
Tests for UI components.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from app.components.backtest.strategy_params import (
    get_strategy_params,
    get_risk_params,
    show_example_calculation
)
from app.components.backtest.results_display import (
    display_performance_metrics,
    display_pattern_analysis,
    display_trade_list
)

@pytest.fixture
def sample_results():
    """Create sample backtest results."""
    return {
        'performance': {
            'total_return': 15.5,
            'max_drawdown': -8.2,
            'win_rate': 65.0,
            'profit_factor': 1.8,
            'completed_trades': 50,
            'avg_trade_return': 0.31,
            'sharpe_ratio': 1.5,
            'max_consecutive_losses': 3
        },
        'trades': [
            {
                'entry_time': datetime(2023, 1, 1),
                'exit_time': datetime(2023, 1, 2),
                'side': 'long',
                'entry_price': 100.0,
                'exit_price': 105.0,
                'pnl': 5.0,
                'return_pct': 5.0
            }
        ],
        'patterns': [
            {
                'type': 'head_and_shoulders',
                'confidence': 0.85,
                'timestamp': datetime(2023, 1, 1),
                'price': 100.0
            }
        ]
    }

def test_strategy_params():
    """Test strategy parameter generation."""
    # Test RSI strategy params
    rsi_params = get_strategy_params('rsi')
    assert 'rsi_period' in rsi_params
    assert 'rsi_overbought' in rsi_params
    assert 'rsi_oversold' in rsi_params
    
    # Test pattern strategy params
    pattern_params = get_strategy_params('patterns')
    assert 'min_pattern_confidence' in pattern_params
    assert 'pattern_lookback' in pattern_params

def test_risk_params():
    """Test risk parameter generation."""
    risk_params = get_risk_params()
    
    assert 'initial_balance' in risk_params
    assert 'risk_per_trade' in risk_params
    assert 'stop_loss_pct' in risk_params
    assert 'risk_reward' in risk_params
    assert 'max_positions' in risk_params
    
    # Validate parameter ranges
    assert 0 < risk_params['risk_per_trade'] <= 0.1  # 1-10%
    assert 0 < risk_params['stop_loss_pct'] <= 0.1   # 1-10%
    assert risk_params['risk_reward'] >= 1.0         # At least 1:1
    assert risk_params['max_positions'] > 0          # At least 1

def test_performance_metrics(sample_results):
    """Test performance metrics display."""
    metrics = sample_results['performance']
    
    # Verify all required metrics are present
    assert 'total_return' in metrics
    assert 'max_drawdown' in metrics
    assert 'win_rate' in metrics
    assert 'profit_factor' in metrics
    assert 'completed_trades' in metrics
    
    # Verify metric calculations
    assert metrics['total_return'] > 0  # Profitable
    assert metrics['max_drawdown'] < 0  # Valid drawdown
    assert 0 <= metrics['win_rate'] <= 100  # Valid percentage
    assert metrics['profit_factor'] > 1  # Profitable ratio

def test_trade_list(sample_results):
    """Test trade list display."""
    trades = sample_results['trades']
    
    for trade in trades:
        # Verify trade structure
        assert 'entry_time' in trade
        assert 'exit_time' in trade
        assert 'side' in trade
        assert 'entry_price' in trade
        assert 'exit_price' in trade
        assert 'pnl' in trade
        assert 'return_pct' in trade
        
        # Verify trade data
        assert trade['exit_time'] > trade['entry_time']
        assert trade['side'] in ['long', 'short']
        assert trade['entry_price'] > 0
        assert trade['exit_price'] > 0
        
        # Verify PnL calculation
        if trade['side'] == 'long':
            expected_pnl = trade['exit_price'] - trade['entry_price']
        else:  # short
            expected_pnl = trade['entry_price'] - trade['exit_price']
        assert abs(trade['pnl'] - expected_pnl) < 0.01

def test_pattern_analysis(sample_results):
    """Test pattern analysis display."""
    patterns = sample_results['patterns']
    
    for pattern in patterns:
        # Verify pattern structure
        assert 'type' in pattern
        assert 'confidence' in pattern
        assert 'timestamp' in pattern
        assert 'price' in pattern
        
        # Verify pattern data
        assert pattern['type'] in [
            'head_and_shoulders',
            'double_top',
            'double_bottom',
            'triangle',
            'flag',
            'wedge'
        ]
        assert 0 <= pattern['confidence'] <= 1
        assert isinstance(pattern['timestamp'], datetime)
        assert pattern['price'] > 0
