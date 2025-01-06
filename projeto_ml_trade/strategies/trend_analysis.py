"""
Trend analysis trading strategy.
"""
from typing import List, Dict
import pandas as pd
from utils.market_regime import MarketRegimeAnalyzer
from utils.logging_helper import LoggingHelper
from .base import BaseStrategy

class TrendAnalysisStrategy(BaseStrategy):
    def __init__(self,
                ema_periods: List[int] = [20, 50, 200],
                slope_period: int = 5,
                lookback: int = 20,
                confidence_threshold: float = 0.6):
        """
        Initialize Trend Analysis strategy.
        
        Args:
            ema_periods: List of EMA periods for trend analysis
            slope_period: Period for slope calculation
            lookback: Period for price action analysis
            confidence_threshold: Minimum confidence level for signals
        """
        super().__init__()
        self.ema_periods = ema_periods
        self.slope_period = slope_period
        self.lookback = lookback
        self.confidence_threshold = confidence_threshold
        self.analyzer = MarketRegimeAnalyzer()
        
        LoggingHelper.log(f"Initialized Trend Analysis Strategy with parameters:")
        LoggingHelper.log(f"EMA Periods: {ema_periods}")
        LoggingHelper.log(f"Slope Period: {slope_period}")
        LoggingHelper.log(f"Lookback: {lookback}")
        LoggingHelper.log(f"Confidence Threshold: {confidence_threshold}")

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on trend analysis.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Get trend analysis
        trend_info = self.analyzer.identify_trend(df, self.ema_periods, self.slope_period)
        
        # Get price action analysis
        price_action = self.analyzer.analyze_price_action(df, self.lookback)
        
        # Get support/resistance levels
        support, resistance = self.analyzer.get_support_resistance(df)
        
        # Calculate base confidence from trend strength
        base_confidence = 0.6
        if trend_info['trend'] in ['strong_bullish', 'strong_bearish']:
            base_confidence *= 1.2
        elif trend_info['trend'] in ['weak_bullish', 'weak_bearish']:
            base_confidence *= 0.9
            
        # Adjust confidence based on price action
        if price_action['is_trending']:
            base_confidence *= 1.1
            
        confidence = min(base_confidence, 1.0)
        
        # Generate signals based on trend analysis
        if trend_info['trend'] in ['strong_bullish', 'weak_bullish']:
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'long',
                    'confidence': confidence,
                    'price': df['close'].iloc[-1],
                    'pattern': f"trend_{trend_info['trend']}",
                    'support': support
                })
                LoggingHelper.log(f"Generated bullish trend signal with confidence {confidence:.2f}")
                
        elif trend_info['trend'] in ['strong_bearish', 'weak_bearish']:
            if confidence >= self.confidence_threshold:
                signals.append({
                    'type': 'short',
                    'confidence': confidence,
                    'price': df['close'].iloc[-1],
                    'pattern': f"trend_{trend_info['trend']}",
                    'resistance': resistance
                })
                LoggingHelper.log(f"Generated bearish trend signal with confidence {confidence:.2f}")
        
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
            
        # Get trend analysis
        trend_info = self.analyzer.identify_trend(
            df.iloc[:current_idx + 1],
            self.ema_periods,
            self.slope_period
        )
        
        # Exit long position
        if position['type'] == 'long':
            if trend_info['trend'] in ['strong_bearish', 'weak_bearish']:
                LoggingHelper.log("Exiting long position on bearish trend")
                return True
                
        # Exit short position
        elif position['type'] == 'short':
            if trend_info['trend'] in ['strong_bullish', 'weak_bullish']:
                LoggingHelper.log("Exiting short position on bullish trend")
                return True
        
        return False

    def calculate_position_size(self, df: pd.DataFrame, signal: Dict) -> float:
        """
        Calculate position size based on trend strength.
        
        Args:
            df: DataFrame with price data
            signal: Signal dictionary with confidence level
            
        Returns:
            float: Position size multiplier (0.0 to 1.0)
        """
        # Base size from signal confidence
        base_size = 0.5
        
        # Get trend analysis
        trend_info = self.analyzer.identify_trend(df, self.ema_periods, self.slope_period)
        
        # Adjust based on trend strength
        trend_multiplier = 1.0
        if trend_info['trend'].startswith('strong'):
            trend_multiplier = 1.2
        elif trend_info['trend'].startswith('weak'):
            trend_multiplier = 0.8
            
        # Adjust based on slope alignment
        if (signal['type'] == 'long' and trend_info['slopes_bullish']) or \
           (signal['type'] == 'short' and trend_info['slopes_bearish']):
            trend_multiplier *= 1.1
        
        return min(base_size * trend_multiplier * signal['confidence'], 1.0)
