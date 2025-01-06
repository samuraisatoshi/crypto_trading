"""
MACD (Moving Average Convergence Divergence) strategy implementation.
"""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from utils.indicators import calculate_macd
from utils.logging_helper import LoggingHelper
from .base import BaseStrategy

class MACDStrategy(BaseStrategy):
    def __init__(self,
                fast_period: int = 12,
                slow_period: int = 26,
                signal_period: int = 9,
                min_histogram: float = 0.0,
                confidence_threshold: float = 0.6):
        """
        Initialize MACD strategy.
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            min_histogram: Minimum histogram value for signal generation
            confidence_threshold: Minimum confidence level for signals
        """
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.min_histogram = min_histogram
        self.confidence_threshold = confidence_threshold
        
        LoggingHelper.log(f"Initialized MACD Strategy with parameters:")
        LoggingHelper.log(f"Fast Period: {fast_period}")
        LoggingHelper.log(f"Slow Period: {slow_period}")
        LoggingHelper.log(f"Signal Period: {signal_period}")
        LoggingHelper.log(f"Min Histogram: {min_histogram}")
        LoggingHelper.log(f"Confidence Threshold: {confidence_threshold}")

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on MACD indicator.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Calculate MACD
        macd_data = calculate_macd(
            df['close'],
            self.fast_period,
            self.slow_period,
            self.signal_period
        )
        
        df['macd'] = macd_data['macd']
        df['signal'] = macd_data['signal']
        df['histogram'] = macd_data['histogram']
        
        # Get current values
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for crossovers
        current_cross = current['macd'] - current['signal']
        previous_cross = previous['macd'] - previous['signal']
        
        # Calculate confidence based on histogram strength
        confidence = min(
            abs(current['histogram']) / (abs(current['macd']) + 1e-9),
            1.0
        )
        
        # Bullish signal conditions
        if (previous_cross <= 0 and current_cross > 0 and  # Bullish crossover
            abs(current['histogram']) >= self.min_histogram and  # Minimum histogram
            confidence >= self.confidence_threshold):  # Sufficient confidence
            
            signals.append({
                'type': 'long',
                'confidence': confidence,
                'price': current['close'],
                'pattern': 'macd_bullish_cross'
            })
            LoggingHelper.log(f"Generated bullish signal with confidence {confidence:.2f}")
        
        # Bearish signal conditions
        elif (previous_cross >= 0 and current_cross < 0 and  # Bearish crossover
              abs(current['histogram']) >= self.min_histogram and  # Minimum histogram
              confidence >= self.confidence_threshold):  # Sufficient confidence
            
            signals.append({
                'type': 'short',
                'confidence': confidence,
                'price': current['close'],
                'pattern': 'macd_bearish_cross'
            })
            LoggingHelper.log(f"Generated bearish signal with confidence {confidence:.2f}")
        
        return signals

    def should_exit(self, df: pd.DataFrame, current_idx: int, position: Dict) -> bool:
        """
        Determine if current position should be exited.
        
        Args:
            df: DataFrame with price data
            current_idx: Current index in DataFrame
            position: Current position information
            
        Returns:
            bool: True if position should be exited
        """
        if current_idx < 1:
            return False
            
        current = df.iloc[current_idx]
        previous = df.iloc[current_idx - 1]
        
        # Calculate current and previous crossovers
        current_cross = current['macd'] - current['signal']
        previous_cross = previous['macd'] - previous['signal']
        
        # Exit long position on bearish crossover
        if position['type'] == 'long' and previous_cross >= 0 and current_cross < 0:
            LoggingHelper.log("Exiting long position on bearish crossover")
            return True
            
        # Exit short position on bullish crossover
        if position['type'] == 'short' and previous_cross <= 0 and current_cross > 0:
            LoggingHelper.log("Exiting short position on bullish crossover")
            return True
            
        return False

    def calculate_position_size(self, df: pd.DataFrame, signal: Dict) -> float:
        """
        Calculate position size based on signal confidence.
        
        Args:
            df: DataFrame with price data
            signal: Signal dictionary with confidence level
            
        Returns:
            float: Position size multiplier (0.0 to 1.0)
        """
        # Scale position size based on signal confidence
        base_size = 0.5  # Base position size
        confidence_multiplier = signal['confidence']
        
        return base_size * confidence_multiplier
