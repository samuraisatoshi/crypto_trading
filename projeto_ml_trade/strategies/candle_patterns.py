"""
Candlestick pattern trading strategy.
"""
from typing import List, Dict
import pandas as pd
from utils.patterns import add_candlestick_patterns
from utils.logging_helper import LoggingHelper
from .base import BaseStrategy

class CandlePatternStrategy(BaseStrategy):
    def __init__(self,
                confidence_threshold: float = 0.6):
        """
        Initialize Candle Pattern strategy.
        
        Args:
            confidence_threshold: Minimum confidence level for signals
        """
        super().__init__()
        self.confidence_threshold = confidence_threshold
        
        LoggingHelper.log(f"Initialized Candle Pattern Strategy with parameters:")
        LoggingHelper.log(f"Confidence Threshold: {confidence_threshold}")

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on candlestick patterns.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Find patterns
        df = add_candlestick_patterns(df)
        
        # Get current values
        current = df.iloc[-1]
        
        # Calculate base confidence
        base_confidence = 0.6  # Base confidence level
        
        # Generate signals based on patterns
        if current['hammer']:
            confidence = base_confidence * 1.1  # Increase confidence for hammer
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'long',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': 'hammer'
                })
                LoggingHelper.log(f"Generated hammer signal with confidence {confidence:.2f}")
                
        if current['shooting_star']:
            confidence = base_confidence * 1.1
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'short',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': 'shooting_star'
                })
                LoggingHelper.log(f"Generated shooting star signal with confidence {confidence:.2f}")
                
        if current['engulfing'] == 'bullish':
            confidence = base_confidence * 1.2  # Higher confidence for engulfing
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'long',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': 'bullish_engulfing'
                })
                LoggingHelper.log(f"Generated bullish engulfing signal with confidence {confidence:.2f}")
                
        if current['engulfing'] == 'bearish':
            confidence = base_confidence * 1.2
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'short',
                    'confidence': confidence,
                    'price': current['close'],
                    'pattern': 'bearish_engulfing'
                })
                LoggingHelper.log(f"Generated bearish engulfing signal with confidence {confidence:.2f}")
        
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
            
        # Find patterns
        df = add_candlestick_patterns(df.iloc[:current_idx + 1])
        current = df.iloc[-1]
        
        # Exit long position
        if position['type'] == 'long':
            if (current['shooting_star'] or  # Strong bearish pattern
                current['engulfing'] == 'bearish'):  # Bearish engulfing
                LoggingHelper.log("Exiting long position on bearish pattern")
                return True
                
        # Exit short position
        elif position['type'] == 'short':
            if (current['hammer'] or  # Strong bullish pattern
                current['engulfing'] == 'bullish'):  # Bullish engulfing
                LoggingHelper.log("Exiting short position on bullish pattern")
                return True
        
        return False

    def calculate_position_size(self, df: pd.DataFrame, signal: Dict) -> float:
        """
        Calculate position size based on pattern strength.
        
        Args:
            df: DataFrame with price data
            signal: Signal dictionary with confidence level
            
        Returns:
            float: Position size multiplier (0.0 to 1.0)
        """
        # Base size from signal confidence
        base_size = 0.5
        
        # Adjust based on pattern type
        pattern_multiplier = 1.0
        if signal['pattern'] in ['bullish_engulfing', 'bearish_engulfing']:
            pattern_multiplier = 1.2  # Increase size for engulfing patterns
        elif signal['pattern'] in ['hammer', 'shooting_star']:
            pattern_multiplier = 1.1  # Slight increase for hammer/shooting star
            
        return min(base_size * pattern_multiplier * signal['confidence'], 1.0)
