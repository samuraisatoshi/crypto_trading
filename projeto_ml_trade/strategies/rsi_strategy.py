"""
RSI-based trading strategy.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from utils.logging_helper import LoggingHelper
from strategies.base import BaseStrategy

class RSIStrategy(BaseStrategy):
    """Trading strategy based on RSI indicator."""
    
    def __init__(self, **kwargs):
        """Initialize strategy."""
        super().__init__(**kwargs)
        self.rsi_period = kwargs.get('rsi_period', 14)
        self.rsi_overbought = kwargs.get('rsi_overbought', 70)
        self.rsi_oversold = kwargs.get('rsi_oversold', 30)
    
    def generate_signals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate trading signals."""
        try:
            # Need at least RSI period + 1 bars
            if len(df) <= self.rsi_period:
                return []
            
            # Calculate RSI
            close_diff = df['close'].diff()
            gains = close_diff.where(close_diff > 0, 0)
            losses = -close_diff.where(close_diff < 0, 0)
            
            avg_gain = gains.rolling(window=self.rsi_period, min_periods=1).mean()
            avg_loss = losses.rolling(window=self.rsi_period, min_periods=1).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            signals = []
            current_bar = df.iloc[-1]
            current_rsi = rsi.iloc[-1]
            
            # Generate signals
            if current_rsi <= self.rsi_oversold:
                signal = {
                    'timestamp': current_bar['timestamp'] if 'timestamp' in current_bar else current_bar.name,
                    'type': 'entry',
                    'side': 'long',
                    'price': current_bar['close'],
                    'rsi': current_rsi
                }
                
                if self.validate_signal(signal):
                    # Calculate stop loss and take profit
                    stop_loss = self.calculate_stop_loss(signal['price'])
                    take_profit = self.calculate_take_profit(signal['price'], stop_loss)
                    
                    signal['stop_loss'] = stop_loss
                    signal['take_profit'] = take_profit
                    
                    signals.append(signal)
                    self._log_signal(signal)
                    LoggingHelper.log(f"RSI Oversold: {current_rsi:.1f}")
            
            elif current_rsi >= self.rsi_overbought:
                signal = {
                    'timestamp': current_bar['timestamp'] if 'timestamp' in current_bar else current_bar.name,
                    'type': 'entry',
                    'side': 'short',
                    'price': current_bar['close'],
                    'rsi': current_rsi
                }
                
                if self.validate_signal(signal):
                    # Calculate stop loss and take profit
                    stop_loss = self.calculate_stop_loss(signal['price'])
                    take_profit = self.calculate_take_profit(signal['price'], stop_loss)
                    
                    signal['stop_loss'] = stop_loss
                    signal['take_profit'] = take_profit
                    
                    signals.append(signal)
                    self._log_signal(signal)
                    LoggingHelper.log(f"RSI Overbought: {current_rsi:.1f}")
            
            return signals
            
        except Exception as e:
            LoggingHelper.log(f"Error in RSI strategy: {str(e)}")
            return []
    
    def calculate_stop_loss(self, entry_price: float, pattern: Dict[str, Any] = None) -> float:
        """Calculate stop loss price."""
        # Use fixed percentage for RSI strategy
        return entry_price * (1 - self.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float) -> float:
        """Calculate take profit price."""
        # Use risk/reward ratio
        risk = abs(entry_price - stop_loss)
        reward = risk * self.risk_reward_ratio
        return entry_price + reward
