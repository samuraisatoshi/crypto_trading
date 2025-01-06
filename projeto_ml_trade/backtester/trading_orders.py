"""
Trading orders for backtesting.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum, auto

class OrderType(Enum):
    """Order types."""
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()

class OrderSide(Enum):
    """Order sides."""
    BUY = auto()
    SELL = auto()
    LONG = auto()
    SHORT = auto()

class OrderStatus(Enum):
    """Order statuses."""
    PENDING = auto()
    FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()

@dataclass
class Order:
    """Trading order."""
    type: str  # 'long', 'short', 'buy', 'sell'
    size: float
    price: float
    time: datetime
    pattern: Optional[str] = None
    confidence: Optional[float] = None
    
    def __post_init__(self):
        """Validate order after initialization."""
        # Validate order type
        valid_types = ['long', 'short', 'buy', 'sell']
        if self.type not in valid_types:
            raise ValueError(f"Invalid order type: {self.type}")
        
        # Validate size
        if self.size <= 0:
            raise ValueError(f"Invalid order size: {self.size}")
        
        # Validate price
        if self.price <= 0:
            raise ValueError(f"Invalid order price: {self.price}")
        
        # Validate time
        if not isinstance(self.time, datetime):
            raise ValueError(f"Invalid order time: {self.time}")
        
        # Validate confidence if provided
        if self.confidence is not None and not (0 <= self.confidence <= 1):
            raise ValueError(f"Invalid confidence value: {self.confidence}")

class TradingOrders:
    """Trading orders manager."""
    
    def __init__(self):
        """Initialize trading orders manager."""
        self.orders = []
        self.filled_orders = []
        self.cancelled_orders = []
    
    def create_order(self,
                    side: OrderSide,
                    type: OrderType,
                    size: float,
                    price: float,
                    time: datetime,
                    pattern: Optional[str] = None,
                    confidence: Optional[float] = None) -> Order:
        """
        Create a new order.
        
        Args:
            side: Order side (BUY, SELL, LONG, SHORT)
            type: Order type (MARKET, LIMIT, STOP, STOP_LIMIT)
            size: Order size
            price: Order price
            time: Order time
            pattern: Optional pattern that triggered order
            confidence: Optional confidence level
            
        Returns:
            Order: Created order
        """
        order = Order(
            type=side.name.lower(),
            size=size,
            price=price,
            time=time,
            pattern=pattern,
            confidence=confidence
        )
        self.orders.append(order)
        return order
    
    def fill_order(self, order: Order):
        """
        Mark order as filled.
        
        Args:
            order: Order to fill
        """
        if order in self.orders:
            self.orders.remove(order)
            self.filled_orders.append(order)
    
    def cancel_order(self, order: Order):
        """
        Cancel order.
        
        Args:
            order: Order to cancel
        """
        if order in self.orders:
            self.orders.remove(order)
            self.cancelled_orders.append(order)
    
    def get_open_orders(self) -> list:
        """
        Get open orders.
        
        Returns:
            list: List of open orders
        """
        return self.orders.copy()
    
    def get_filled_orders(self) -> list:
        """
        Get filled orders.
        
        Returns:
            list: List of filled orders
        """
        return self.filled_orders.copy()
    
    def get_cancelled_orders(self) -> list:
        """
        Get cancelled orders.
        
        Returns:
            list: List of cancelled orders
        """
        return self.cancelled_orders.copy()
    
    def reset(self):
        """Reset orders state."""
        self.orders = []
        self.filled_orders = []
        self.cancelled_orders = []
