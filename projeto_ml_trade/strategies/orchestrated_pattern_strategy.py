"""
Pattern-based trading strategy using multiple pattern detectors.
"""
import pandas as pd
from typing import List, Dict, Any, Tuple

from utils.logging_helper import LoggingHelper
from strategies.base import BaseStrategy
from strategies.pattern_orchestrator import PatternOrchestrator

class OrchestratedPatternStrategy(BaseStrategy):
    """Trading strategy based on multiple chart patterns."""
    
    def __init__(self, **kwargs):
        """Initialize strategy."""
        super().__init__(**kwargs)
        self.orchestrator = PatternOrchestrator()
        self.min_confidence = kwargs.get('min_confidence', 0.7)
        self.risk_reward_ratio = kwargs.get('risk_reward_ratio', 2.0)
    
    def generate_signals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate trading signals from detected patterns."""
        try:
            # Detect patterns
            patterns = self.orchestrator.detect_patterns(df, self.min_confidence)
            
            if not patterns:
                return []
            
            # Filter and resolve conflicts
            filtered_patterns = self.orchestrator.filter_patterns(patterns, self.min_confidence)
            resolved_patterns = self.orchestrator.resolve_conflicts(filtered_patterns)
            
            # Generate signals
            signals = []
            for pattern in resolved_patterns:
                try:
                    # Get pattern points
                    points = pattern['points']
                    pattern_end = max(p['timestamp'] for p in points)
                    entry_price = pattern['price']
                    
                    # Calculate stop loss and take profit
                    stop_loss = self.calculate_stop_loss(entry_price, pattern)
                    take_profit = self.calculate_take_profit(entry_price, stop_loss)
                    
                    # Create signal
                    signal = {
                        'timestamp': pattern_end,
                        'type': 'entry',
                        'side': self.orchestrator._get_pattern_direction(pattern),
                        'price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'confidence': pattern['confidence'],
                        'pattern': pattern['type']
                    }
                    
                    signals.append(signal)
                    LoggingHelper.log(
                        f"Generated {signal['side']} signal from {pattern['type']} pattern "
                        f"(Entry: {entry_price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f})"
                    )
                except Exception as e:
                    LoggingHelper.log(f"Error generating signal from pattern: {str(e)}")
                    continue
            
            return signals
        
        except Exception as e:
            LoggingHelper.log(f"Error in pattern strategy: {str(e)}")
            return []
    
    def calculate_stop_loss(self, entry_price: float, pattern: Dict[str, Any]) -> float:
        """Calculate stop loss price based on pattern."""
        try:
            # Get pattern points
            points = pattern['points']
            prices = [p['price'] for p in points]
            
            # Calculate based on pattern volatility
            price_range = max(prices) - min(prices)
            pattern_low = min(prices)
            
            if pattern['type'] in ['head_and_shoulders', 'double_top', 'descending_triangle']:
                # Bearish patterns - stop above pattern high
                return entry_price + (price_range * 0.5)
            else:
                # Bullish patterns - stop below pattern low
                return max(pattern_low * 0.99, entry_price - (price_range * 0.5))
            
        except Exception as e:
            LoggingHelper.log(f"Error calculating stop loss: {str(e)}")
            # Default to 2% stop loss
            return entry_price * 0.98
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float) -> float:
        """Calculate take profit price based on risk/reward ratio."""
        try:
            risk = abs(entry_price - stop_loss)
            reward = risk * self.risk_reward_ratio
            
            if stop_loss < entry_price:  # Long position
                return entry_price + reward
            else:  # Short position
                return entry_price - reward
            
        except Exception as e:
            LoggingHelper.log(f"Error calculating take profit: {str(e)}")
            # Default to 2x risk/reward
            return entry_price * 1.04  # 4% target
