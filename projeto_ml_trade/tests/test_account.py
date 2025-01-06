"""
Tests for trading account functionality.
"""
import pytest
from decimal import Decimal
from backtester.account import Account
from backtester.trading_orders import Order, Position

@pytest.fixture
def account():
    """Create trading account for testing."""
    return Account(initial_balance=10000)

@pytest.fixture
def sample_position(account):
    """Create sample position for testing."""
    return Position(
        account=account,
        side='long',
        size=1.0,
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        timestamp='2023-01-01 00:00:00'
    )

class TestAccount:
    """Test suite for trading account functionality."""
    
    def test_initialization(self, account):
        """Test account initialization."""
        assert account.initial_balance == 10000
        assert account.balance == 10000
        assert account.equity == 10000
        assert len(account.positions) == 0
        assert len(account.closed_positions) == 0
        assert account.max_drawdown == 0
    
    def test_add_position(self, account, sample_position):
        """Test adding position to account."""
        # Add position
        account.add_position(sample_position)
        
        assert len(account.positions) == 1
        assert account.positions[0] == sample_position
        
        # Check margin allocation
        position_margin = sample_position.size * sample_position.entry_price
        assert account.balance == 10000 - position_margin
        
        # Check equity calculation
        expected_equity = account.balance + position_margin
        assert abs(account.equity - expected_equity) < 0.01
    
    def test_remove_position(self, account, sample_position):
        """Test removing position from account."""
        # Add and then remove position
        account.add_position(sample_position)
        account.remove_position(sample_position)
        
        assert len(account.positions) == 0
        assert len(account.closed_positions) == 1
        assert account.balance == 10000  # Balance should be restored
    
    def test_position_pnl(self, account, sample_position):
        """Test position profit/loss calculation."""
        account.add_position(sample_position)
        
        # Test profit scenario
        current_price = 105.0
        expected_pnl = (current_price - sample_position.entry_price) * sample_position.size
        actual_pnl = sample_position.calculate_pnl(current_price)
        assert abs(actual_pnl - expected_pnl) < 0.01
        
        # Test loss scenario
        current_price = 97.0
        expected_pnl = (current_price - sample_position.entry_price) * sample_position.size
        actual_pnl = sample_position.calculate_pnl(current_price)
        assert abs(actual_pnl - expected_pnl) < 0.01
    
    def test_equity_updates(self, account, sample_position):
        """Test equity updates with position changes."""
        initial_equity = account.equity
        
        # Add position
        account.add_position(sample_position)
        position_value = sample_position.size * sample_position.entry_price
        assert account.equity == initial_equity
        
        # Update with profit
        profit = 500
        sample_position.update_pnl(profit)
        assert account.equity == initial_equity + profit
        
        # Update with loss
        loss = -300
        sample_position.update_pnl(loss)
        assert account.equity == initial_equity + loss
    
    def test_drawdown_calculation(self, account, sample_position):
        """Test maximum drawdown calculation."""
        initial_equity = account.equity
        
        # Add position
        account.add_position(sample_position)
        
        # Simulate drawdown
        losses = [-100, -200, -300, -150, -50]
        max_drawdown = 0
        peak_equity = initial_equity
        
        for loss in losses:
            sample_position.update_pnl(loss)
            current_equity = account.equity
            drawdown = (peak_equity - current_equity) / peak_equity
            max_drawdown = min(max_drawdown, drawdown)
            
            assert account.max_drawdown <= max_drawdown
            
            if current_equity > peak_equity:
                peak_equity = current_equity
    
    def test_position_limits(self, account):
        """Test position size and risk limits."""
        # Test maximum position size
        max_position_size = account.initial_balance * 0.5  # 50% of balance
        
        # Valid position
        valid_position = Position(
            account=account,
            side='long',
            size=max_position_size / 100,  # Assuming price of 100
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            timestamp='2023-01-01 00:00:00'
        )
        account.add_position(valid_position)
        
        # Invalid position (too large)
        with pytest.raises(ValueError):
            invalid_position = Position(
                account=account,
                side='long',
                size=account.initial_balance * 2 / 100,  # Position larger than balance
                entry_price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
            account.add_position(invalid_position)
    
    def test_position_validation(self, account):
        """Test position validation rules."""
        # Test invalid side
        with pytest.raises(ValueError):
            Position(
                account=account,
                side='invalid',
                size=1.0,
                entry_price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
        
        # Test invalid price relationships
        with pytest.raises(ValueError):
            Position(
                account=account,
                side='long',
                size=1.0,
                entry_price=100.0,
                stop_loss=105.0,  # Stop loss above entry for long position
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
        
        with pytest.raises(ValueError):
            Position(
                account=account,
                side='long',
                size=1.0,
                entry_price=100.0,
                stop_loss=95.0,
                take_profit=90.0,  # Take profit below entry for long position
                timestamp='2023-01-01 00:00:00'
            )
    
    def test_account_history(self, account, sample_position):
        """Test account history tracking."""
        # Add position
        account.add_position(sample_position)
        
        # Update position with various PnL values
        updates = [100, -50, 200, -100, 300]
        
        for pnl in updates:
            sample_position.update_pnl(pnl)
            
            # Check history entry
            latest_history = account.history[-1]
            assert 'timestamp' in latest_history
            assert 'equity' in latest_history
            assert 'balance' in latest_history
            assert 'positions' in latest_history
            
            # Verify history values
            assert latest_history['equity'] == account.equity
            assert latest_history['balance'] == account.balance
            assert len(latest_history['positions']) == len(account.positions)
