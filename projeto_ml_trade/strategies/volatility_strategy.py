"""
Volatility-based trading strategy.
"""
from typing import List, Dict
import pandas as pd
from utils.volatility_metrics import VolatilityAnalyzer
from utils.logging_helper import LoggingHelper
from .base import BaseStrategy

class VolatilityStrategy(BaseStrategy):
    def __init__(self,
                atr_period: int = 14,
                bb_period: int = 20,
                bb_std: float = 2.0,
                vol_lookback: int = 20,
                vol_threshold: float = 1.5,
                range_threshold: float = 0.8,
                confidence_threshold: float = 0.6):
        """
        Initialize Volatility strategy.
        
        Args:
            atr_period: Period for ATR calculation
            bb_period: Period for Bollinger Bands
            bb_std: Standard deviations for Bollinger Bands
            vol_lookback: Lookback period for volatility comparison
            vol_threshold: Minimum volatility expansion ratio
            range_threshold: Minimum candle range as % of ATR
            confidence_threshold: Minimum confidence level for signals
        """
        super().__init__()
        self.atr_period = atr_period
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.vol_lookback = vol_lookback
        self.vol_threshold = vol_threshold
        self.range_threshold = range_threshold
        self.confidence_threshold = confidence_threshold
        self.analyzer = VolatilityAnalyzer()
        
        LoggingHelper.log(f"Initialized Volatility Strategy with parameters:")
        LoggingHelper.log(f"ATR Period: {atr_period}")
        LoggingHelper.log(f"BB Period: {bb_period}")
        LoggingHelper.log(f"BB Std: {bb_std}")
        LoggingHelper.log(f"Volatility Lookback: {vol_lookback}")
        LoggingHelper.log(f"Volatility Threshold: {vol_threshold}")
        LoggingHelper.log(f"Range Threshold: {range_threshold}")
        LoggingHelper.log(f"Confidence Threshold: {confidence_threshold}")

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on volatility analysis.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Get volatility analysis
        vol_analysis = self.analyzer.analyze_volatility(
            df,
            self.vol_lookback,
            self.atr_period,
            self.bb_period,
            self.bb_std
        )
        
        # Detect breakout
        breakout = self.analyzer.detect_breakout(df)
        
        # Calculate volatility score
        vol_score = self.analyzer.calculate_volatility_score(
            df,
            self.vol_threshold,
            self.range_threshold
        )
        
        # Generate signals based on volatility and breakouts
        if breakout == 'up' and vol_analysis['is_high_vol']:
            if vol_score >= self.confidence_threshold:
                signals.append({
                    'type': 'long',
                    'confidence': vol_score,
                    'price': df['close'].iloc[-1],
                    'pattern': 'volatility_breakout_up',
                    'atr': df['atr'].iloc[-1]
                })
                LoggingHelper.log(f"Generated bullish breakout signal with confidence {vol_score:.2f}")
                
        elif breakout == 'down' and vol_analysis['is_high_vol']:
            if vol_score >= self.confidence_threshold:
                signals.append({
                    'type': 'short',
                    'confidence': vol_score,
                    'price': df['close'].iloc[-1],
                    'pattern': 'volatility_breakout_down',
                    'atr': df['atr'].iloc[-1]
                })
                LoggingHelper.log(f"Generated bearish breakout signal with confidence {vol_score:.2f}")
        
        # Mean reversion signals in squeeze conditions
        elif vol_analysis['is_squeeze']:
            if vol_analysis['bb_position'] > 0.9:  # Near upper band
                signals.append({
                    'type': 'short',
                    'confidence': vol_score * 0.8,  # Lower confidence for mean reversion
                    'price': df['close'].iloc[-1],
                    'pattern': 'volatility_mean_reversion_high',
                    'atr': df['atr'].iloc[-1]
                })
                LoggingHelper.log(f"Generated mean reversion short signal with confidence {vol_score*0.8:.2f}")
                
            elif vol_analysis['bb_position'] < 0.1:  # Near lower band
                signals.append({
                    'type': 'long',
                    'confidence': vol_score * 0.8,
                    'price': df['close'].iloc[-1],
                    'pattern': 'volatility_mean_reversion_low',
                    'atr': df['atr'].iloc[-1]
                })
                LoggingHelper.log(f"Generated mean reversion long signal with confidence {vol_score*0.8:.2f}")
        
        return signals

    def should_exit(self, df: pd.DataFrame, current_idx: int, position: Dict) -> bool:
        """
        Determine if current position should be exited based on volatility.
        
        Args:
            df: DataFrame with price data
            current_idx: Current index in DataFrame
            position: Current position information
            
        Returns:
            bool: True if position should be exited
        """
        if current_idx < 1:
            return False
            
        # Get volatility analysis
        vol_analysis = self.analyzer.analyze_volatility(
            df.iloc[:current_idx + 1],
            self.vol_lookback,
            self.atr_period,
            self.bb_period,
            self.bb_std
        )
        
        current = df.iloc[current_idx]
        
        # Exit long position
        if position['type'] == 'long':
            # Exit on volatility contraction or mean reversion
            if (vol_analysis['vol_ratio'] < 0.7 or  # Significant contraction
                current['close'] < current['bb_middle']):  # Below middle band
                LoggingHelper.log("Exiting long position on volatility contraction")
                return True
                
        # Exit short position
        elif position['type'] == 'short':
            # Exit on volatility contraction or mean reversion
            if (vol_analysis['vol_ratio'] < 0.7 or  # Significant contraction
                current['close'] > current['bb_middle']):  # Above middle band
                LoggingHelper.log("Exiting short position on volatility contraction")
                return True
        
        return False

    def calculate_position_size(self, df: pd.DataFrame, signal: Dict) -> float:
        """
        Calculate position size based on volatility conditions.
        
        Args:
            df: DataFrame with price data
            signal: Signal dictionary with confidence level
            
        Returns:
            float: Position size multiplier (0.0 to 1.0)
        """
        return self.analyzer.adjust_position_size(0.5, df, self.vol_threshold)
