"""
Tests for backtesting functionality.
"""
import pytest
import pandas as pd
import numpy as np
from backtester.backtester import Backtester
from backtester.account import Account
from backtester.trading_orders import Order, Position
from strategies.pattern_strategy import PatternStrategy
from strategies.rsi_strategy import RSIStrategy

@pytest.fixture
def backtester(sample_ohlcv_data):
    """Create backtester instance with sample data."""
    return Backtester(
        df=sample_ohlcv_data,
        strategy_id='patterns',
        initial_balance=10000,
        risk_per_trade=0.02,
        max_positions=3
    )

@pytest.fixture
def account():
    """Create trading account for testing."""
    return Account(initial_balance=10000)

class TestBacktester:
    """Test suite for backtesting functionality."""
    
    def test_initialization(self, backtester, sample_ohlcv_data):
        """Test backtester initialization."""
        assert backtester.df is not None
        assert len(backtester.df) == len(sample_ohlcv_data)
        assert backtester.initial_balance == 10000
        assert backtester.risk_per_trade == 0.02
        assert backtester.max_positions == 3
        assert isinstance(backtester.account, Account)
    
    @pytest.mark.parametrize("strategy_id,strategy_class", [
        ('rsi', RSIStrategy),
        ('patterns', PatternStrategy)
    ])
    def test_strategy_loading(self, sample_ohlcv_data, strategy_id, strategy_class):
        """Test strategy loading."""
        backtester = Backtester(
            df=sample_ohlcv_data,
            strategy_id=strategy_id,
            initial_balance=10000
        )
        
        assert backtester.strategy is not None
        assert isinstance(backtester.strategy, strategy_class)
        assert hasattr(backtester.strategy, 'generate_signals')
    
    def test_position_management(self, backtester):
        """Test position management."""
        # Run backtest
        for signals, patterns in backtester.run_backtest_generator():
            # Check position constraints
            assert len(backtester.active_positions) <= backtester.max_positions
            
            # Check position sizes
            for position in backtester.active_positions:
                assert position.size > 0
                assert position.risk <= backtester.risk_per_trade * backtester.initial_balance
                
                # Verify position attributes
                assert isinstance(position.entry_price, float)
                assert isinstance(position.stop_loss, float)
                assert isinstance(position.take_profit, float)
                assert position.stop_loss < position.entry_price < position.take_profit
    
    def test_risk_management(self, backtester):
        """Test risk management rules."""
        max_risk = backtester.risk_per_trade * backtester.initial_balance
        
        for signals, patterns in backtester.run_backtest_generator():
            # Calculate total risk
            total_risk = sum(pos.risk for pos in backtester.active_positions)
            assert total_risk <= max_risk * backtester.max_positions
            
            # Check individual position risk
            for position in backtester.active_positions:
                assert position.risk <= max_risk
                
                # Verify risk calculation
                position_risk = position.size * (position.entry_price - position.stop_loss)
                assert abs(position_risk - position.risk) < 0.01  # Allow small floating point difference
    
    def test_performance_metrics(self, backtester):
        """Test performance metrics calculation."""
        # Run complete backtest
        list(backtester.run_backtest_generator())  # Consume generator
        
        # Get results
        results = backtester.get_results()
        
        # Check metrics
        assert 'performance' in results
        metrics = results['performance']
        
        # Verify required metrics
        required_metrics = [
            'total_return',
            'max_drawdown',
            'win_rate',
            'completed_trades',
            'profit_factor',
            'avg_trade_return',
            'sharpe_ratio',
            'max_consecutive_losses'
        ]
        
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
        
        # Validate metric values
        assert isinstance(metrics['total_return'], float)
        assert isinstance(metrics['max_drawdown'], float)
        assert 0 <= metrics['win_rate'] <= 100
        assert metrics['completed_trades'] >= 0
        assert metrics['max_drawdown'] <= 0
        assert metrics['profit_factor'] >= 0
    
    def test_trade_execution(self, backtester):
        """Test trade execution logic."""
        trades = []
        
        for signals, patterns in backtester.run_backtest_generator():
            if signals:
                for signal in signals:
                    # Verify signal properties
                    assert signal['type'] in ['entry', 'exit']
                    assert signal['side'] in ['long', 'short']
                    assert 'price' in signal
                    assert 'timestamp' in signal
                    
                    trades.append(signal)
                    
                    # Check order creation
                    if signal['type'] == 'entry':
                        assert len(backtester.active_positions) > 0
                        latest_position = backtester.active_positions[-1]
                        assert latest_position.entry_price == signal['price']
                        assert latest_position.side == signal['side']
        
        # Verify trade sequence
        for i in range(1, len(trades)):
            current = trades[i]
            previous = trades[i-1]
            
            # Check timestamps
            assert current['timestamp'] >= previous['timestamp']
            
            # Check prices
            assert current['price'] > 0
            assert previous['price'] > 0
    
    def test_account_updates(self, backtester):
        """Test account balance and equity updates."""
        initial_balance = backtester.account.balance
        previous_equity = initial_balance
        
        for signals, patterns in backtester.run_backtest_generator():
            current_equity = backtester.account.equity
            
            # Check balance constraints
            assert backtester.account.balance <= initial_balance
            assert current_equity > 0
            
            # Check equity calculation
            calculated_equity = backtester.account.balance
            for position in backtester.active_positions:
                calculated_equity += position.unrealized_pnl
            
            assert abs(current_equity - calculated_equity) < 0.01
            previous_equity = current_equity
    
    def test_data_requirements(self, sample_ohlcv_data):
        """Test data validation requirements."""
        # Missing columns
        invalid_df = sample_ohlcv_data.drop(['high', 'low'], axis=1)
        with pytest.raises(ValueError):
            Backtester(df=invalid_df, strategy_id='patterns')
        
        # Invalid values
        invalid_df = sample_ohlcv_data.copy()
        invalid_df.loc[0, 'close'] = -1
        with pytest.raises(ValueError):
            Backtester(df=invalid_df, strategy_id='patterns')
        
        # Non-chronological data
        invalid_df = sample_ohlcv_data.copy()
        invalid_df.iloc[0, invalid_df.columns.get_loc('timestamp')] = pd.Timestamp('2025-01-01')
        with pytest.raises(ValueError):
            Backtester(df=invalid_df, strategy_id='patterns')
    
    def test_parameter_validation(self, sample_ohlcv_data):
        """Test parameter validation."""
        # Invalid initial balance
        with pytest.raises(ValueError):
            Backtester(
                df=sample_ohlcv_data,
                strategy_id='patterns',
                initial_balance=-1000
            )
        
        # Invalid risk per trade
        with pytest.raises(ValueError):
            Backtester(
                df=sample_ohlcv_data,
                strategy_id='patterns',
                risk_per_trade=1.5  # Should be <= 1
            )
        
        # Invalid max positions
        with pytest.raises(ValueError):
            Backtester(
                df=sample_ohlcv_data,
                strategy_id='patterns',
                max_positions=0  # Should be > 0
            )
    
    def test_strategy_parameters(self, sample_ohlcv_data):
        """Test strategy parameter handling."""
        strategy_params = {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        }
        
        backtester = Backtester(
            df=sample_ohlcv_data,
            strategy_id='rsi',
            strategy_params=strategy_params
        )
        
        assert backtester.strategy.params == strategy_params
        
        # Run backtest to ensure parameters are used
        list(backtester.run_backtest_generator())
        results = backtester.get_results()
        assert results is not None
