"""
Tests for trading orders functionality.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from backtester.trading_orders import Order, Position
from backtester.account import Account

@pytest.fixture
def account():
    """Create trading account for testing."""
    return Account(initial_balance=10000)

@pytest.fixture
def sample_order(account):
    """Create sample order for testing."""
    return Order(
        account=account,
        side='long',
        size=1.0,
        price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        timestamp='2023-01-01 00:00:00'
    )

class TestTradingOrders:
    """Test suite for trading orders functionality."""
    
    def test_order_creation(self, account):
        """Test order creation and validation."""
        # Valid order
        order = Order(
            account=account,
            side='long',
            size=1.0,
            price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            timestamp='2023-01-01 00:00:00'
        )
        
        assert order.side == 'long'
        assert order.size == 1.0
        assert order.price == 100.0
        assert order.stop_loss == 95.0
        assert order.take_profit == 110.0
        assert isinstance(order.timestamp, datetime)
        
        # Invalid side
        with pytest.raises(ValueError):
            Order(
                account=account,
                side='invalid',
                size=1.0,
                price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
        
        # Invalid price relationships for long order
        with pytest.raises(ValueError):
            Order(
                account=account,
                side='long',
                size=1.0,
                price=100.0,
                stop_loss=105.0,  # Stop loss above entry
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
        
        # Invalid price relationships for short order
        with pytest.raises(ValueError):
            Order(
                account=account,
                side='short',
                size=1.0,
                price=100.0,
                stop_loss=95.0,  # Stop loss below entry
                take_profit=90.0,
                timestamp='2023-01-01 00:00:00'
            )
    
    def test_order_execution(self, account, sample_order):
        """Test order execution."""
        # Execute order
        position = sample_order.execute()
        
        assert isinstance(position, Position)
        assert position.side == sample_order.side
        assert position.size == sample_order.size
        assert position.entry_price == sample_order.price
        assert position.stop_loss == sample_order.stop_loss
        assert position.take_profit == sample_order.take_profit
        
        # Check account position
        assert len(account.positions) == 1
        assert account.positions[0] == position
        
        # Check margin allocation
        expected_margin = sample_order.size * sample_order.price
        assert account.balance == 10000 - expected_margin
    
    def test_position_creation(self, account):
        """Test position creation from order."""
        # Create and execute order
        order = Order(
            account=account,
            side='long',
            size=1.0,
            price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            timestamp='2023-01-01 00:00:00'
        )
        
        position = order.execute()
        
        # Test position properties
        assert position.account == account
        assert position.side == 'long'
        assert position.size == 1.0
        assert position.entry_price == 100.0
        assert position.stop_loss == 95.0
        assert position.take_profit == 110.0
        assert position.pnl == 0
        assert position.status == 'open'
    
    def test_order_risk_calculation(self, account):
        """Test order risk calculation."""
        order = Order(
            account=account,
            side='long',
            size=1.0,
            price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            timestamp='2023-01-01 00:00:00'
        )
        
        # Calculate expected risk
        risk_per_unit = abs(order.price - order.stop_loss)
        expected_risk = order.size * risk_per_unit
        
        assert order.calculate_risk() == expected_risk
        
        # Test risk percentage
        risk_percentage = (expected_risk / account.balance) * 100
        assert abs(order.calculate_risk_percentage() - risk_percentage) < 0.01
    
    def test_order_reward_calculation(self, account):
        """Test order reward calculation."""
        order = Order(
            account=account,
            side='long',
            size=1.0,
            price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            timestamp='2023-01-01 00:00:00'
        )
        
        # Calculate expected reward
        reward_per_unit = abs(order.take_profit - order.price)
        expected_reward = order.size * reward_per_unit
        
        assert order.calculate_reward() == expected_reward
        
        # Test risk/reward ratio
        risk = order.calculate_risk()
        expected_ratio = expected_reward / risk
        assert abs(order.calculate_risk_reward_ratio() - expected_ratio) < 0.01
    
    def test_order_validation(self, account):
        """Test order validation rules."""
        # Test size validation
        with pytest.raises(ValueError):
            Order(
                account=account,
                side='long',
                size=0,  # Invalid size
                price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
        
        # Test price validation
        with pytest.raises(ValueError):
            Order(
                account=account,
                side='long',
                size=1.0,
                price=-100.0,  # Invalid price
                stop_loss=95.0,
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
        
        # Test risk/reward validation
        with pytest.raises(ValueError):
            Order(
                account=account,
                side='long',
                size=1.0,
                price=100.0,
                stop_loss=99.0,  # Small risk
                take_profit=101.0,  # Small reward
                timestamp='2023-01-01 00:00:00'
            )
    
    def test_order_margin_requirements(self, account):
        """Test order margin requirements."""
        # Test order within margin limits
        valid_order = Order(
            account=account,
            side='long',
            size=1.0,
            price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            timestamp='2023-01-01 00:00:00'
        )
        position = valid_order.execute()
        assert position is not None
        
        # Test order exceeding margin limits
        with pytest.raises(ValueError):
            invalid_order = Order(
                account=account,
                side='long',
                size=1000.0,  # Size requiring more margin than available
                price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                timestamp='2023-01-01 00:00:00'
            )
            invalid_order.execute()
    
    def test_order_timestamps(self, account):
        """Test order timestamp handling."""
        # Test various timestamp formats
        timestamps = [
            '2023-01-01 00:00:00',
            datetime.now(),
            pd.Timestamp('2023-01-01 00:00:00'),
            '2023-01-01T00:00:00Z'
        ]
        
        for ts in timestamps:
            order = Order(
                account=account,
                side='long',
                size=1.0,
                price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                timestamp=ts
            )
            assert isinstance(order.timestamp, datetime)
        
        # Test invalid timestamp
        with pytest.raises(ValueError):
            Order(
                account=account,
                side='long',
                size=1.0,
                price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                timestamp='invalid'
            )
