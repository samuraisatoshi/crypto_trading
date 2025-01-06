"""
Risk management for backtesting.
"""
from typing import Dict, Any
from utils.logging_helper import LoggingHelper

class RiskManager:
    """Manages risk limits and position sizing."""
    
    def __init__(self, risk_per_trade: float = 0.02, max_trades: int = 1):
        """
        Initialize risk manager.
        
        Args:
            risk_per_trade: Maximum risk per trade (0.0 to 1.0)
            max_trades: Maximum concurrent trades
        """
        self.risk_per_trade = risk_per_trade
        self.max_trades = max_trades
        
        LoggingHelper.log(f"Initialized RiskManager with parameters:")
        LoggingHelper.log(f"Risk Per Trade: {risk_per_trade:.1%}")
        LoggingHelper.log(f"Max Trades: {max_trades}")
    
    def check_limits(self, account: Any, signal: Dict[str, Any]) -> bool:
        """
        Check if trade meets risk limits.
        
        Args:
            account: Account instance
            signal: Signal dictionary
            
        Returns:
            bool: True if trade meets limits
        """
        # Check max trades
        if len(account.positions) >= self.max_trades:
            return False
        
        # Check if we have enough equity
        min_equity = 1000  # Minimum equity to trade
        if account.equity < min_equity:
            return False
        
        # Check if signal has minimum confidence
        min_confidence = 0.5
        if signal.get('confidence', 1.0) < min_confidence:
            return False
        
        return True
    
    def adjust_position_size(self, size: float, price: float, equity: float) -> float:
        """
        Adjust position size based on risk limits.
        
        Args:
            size: Initial position size
            price: Entry price
            equity: Current account equity
            
        Returns:
            float: Adjusted position size
        """
        # Calculate maximum position size based on risk
        max_size = (equity * self.risk_per_trade) / price
        
        # Adjust size
        adjusted_size = min(size, max_size)
        
        # Ensure minimum size
        min_size = 0.01
        if adjusted_size < min_size:
            return 0.0
        
        return adjusted_size
    
    def reset(self):
        """Reset risk manager state."""
        pass  # No state to reset
