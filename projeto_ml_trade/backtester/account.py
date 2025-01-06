"""
Account management for backtesting.
"""
from typing import Dict, List, Any
from datetime import datetime
from .trading_orders import Order

class Account:
    """Account for managing positions and balance."""
    
    def __init__(self, initial_balance: float = 10000):
        """Initialize account."""
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.positions: List[Dict] = []
    
    def reset(self):
        """Reset account to initial state."""
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.positions = []
    
    def execute_order(self, order: Order):
        """Execute trading order."""
        try:
            if order.type in ['long', 'buy']:
                # Close short position if exists
                self._close_position('short', order.price, order.time)
                
                # Open long position
                if order.type == 'long':
                    position = {
                        'type': 'long',
                        'size': order.size,
                        'entry_price': order.price,
                        'entry_time': order.time,
                        'pnl': 0
                    }
                    self.positions.append(position)
                    
            elif order.type in ['short', 'sell']:
                # Close long position if exists
                self._close_position('long', order.price, order.time)
                
                # Open short position
                if order.type == 'short':
                    position = {
                        'type': 'short',
                        'size': order.size,
                        'entry_price': order.price,
                        'entry_time': order.time,
                        'pnl': 0
                    }
                    self.positions.append(position)
            
            # Update equity
            self._update_equity(order.price)
            
        except Exception as e:
            print(f"Error executing order: {str(e)}")
    
    def _close_position(self, position_type: str, price: float, time: datetime):
        """Close position of given type."""
        try:
            # Find matching position
            for position in list(self.positions):
                if position['type'] == position_type:
                    # Calculate PnL
                    if position_type == 'long':
                        pnl = (price - position['entry_price']) * position['size']
                    else:  # short
                        pnl = (position['entry_price'] - price) * position['size']
                    
                    # Update balance
                    self.balance += pnl
                    
                    # Update position
                    position['pnl'] = pnl
                    
                    # Remove position
                    self.positions.remove(position)
                    
        except Exception as e:
            print(f"Error closing position: {str(e)}")
    
    def _update_equity(self, current_price: float):
        """Update account equity."""
        try:
            # Start with balance
            equity = self.balance
            
            # Add unrealized PnL
            for position in self.positions:
                if position['type'] == 'long':
                    pnl = (current_price - position['entry_price']) * position['size']
                else:  # short
                    pnl = (position['entry_price'] - current_price) * position['size']
                equity += pnl
            
            self.equity = equity
            
        except Exception as e:
            print(f"Error updating equity: {str(e)}")
