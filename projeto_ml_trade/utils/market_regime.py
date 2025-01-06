"""
Market regime and trend analysis utilities.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from utils.indicators import calculate_ema, calculate_slope
from utils.logging_helper import LoggingHelper

class MarketRegimeAnalyzer:
    """Analyzer for market regime and trend analysis."""
    
    def __init__(self):
        """Initialize market regime analyzer."""
        self.logger = LoggingHelper()
    
    def identify_trend(self,
                      df: pd.DataFrame,
                      ema_periods: List[int] = [20, 50, 200],
                      slope_period: int = 5) -> Dict[str, any]:
        """
        Identify market trend using multiple EMAs and slope analysis.
        
        Args:
            df: DataFrame with price data
            ema_periods: List of EMA periods to use
            slope_period: Period for slope calculation
            
        Returns:
            Dictionary with trend analysis results
        """
        # Calculate EMAs
        emas = {}
        slopes = {}
        for period in ema_periods:
            ema = calculate_ema(df['close'], period)
            emas[f'ema_{period}'] = ema
            slopes[f'slope_{period}'] = calculate_slope(ema, slope_period)
        
        current = df.iloc[-1]
        
        # Check EMA alignment
        is_aligned_bullish = True
        is_aligned_bearish = True
        prev_ema = None
        
        for period in ema_periods:
            current_ema = emas[f'ema_{period}'].iloc[-1]
            if prev_ema is not None:
                if current_ema <= prev_ema:  # Not aligned bullish
                    is_aligned_bullish = False
                if current_ema >= prev_ema:  # Not aligned bearish
                    is_aligned_bearish = False
            prev_ema = current_ema
        
        # Check slope alignment
        slopes_bullish = all(slopes[f'slope_{period}'].iloc[-1] > 0 for period in ema_periods)
        slopes_bearish = all(slopes[f'slope_{period}'].iloc[-1] < 0 for period in ema_periods)
        
        # Determine trend strength
        if is_aligned_bullish and slopes_bullish:
            trend_strength = 'strong_bullish'
        elif is_aligned_bearish and slopes_bearish:
            trend_strength = 'strong_bearish'
        elif is_aligned_bullish or slopes_bullish:
            trend_strength = 'weak_bullish'
        elif is_aligned_bearish or slopes_bearish:
            trend_strength = 'weak_bearish'
        else:
            trend_strength = 'neutral'
        
        return {
            'trend': trend_strength,
            'ema_aligned_bullish': is_aligned_bullish,
            'ema_aligned_bearish': is_aligned_bearish,
            'slopes_bullish': slopes_bullish,
            'slopes_bearish': slopes_bearish
        }

    def analyze_price_action(self,
                           df: pd.DataFrame,
                           lookback: int = 20) -> Dict[str, any]:
        """
        Analyze recent price action characteristics.
        
        Args:
            df: DataFrame with price data
            lookback: Period for analysis
            
        Returns:
            Dictionary with price action analysis
        """
        recent_data = df.tail(lookback)
        
        # Calculate swing points
        highs = recent_data['high']
        lows = recent_data['low']
        
        higher_highs = (highs > highs.shift(1)).sum()
        lower_lows = (lows < lows.shift(1)).sum()
        
        # Calculate average range
        ranges = recent_data['high'] - recent_data['low']
        avg_range = ranges.mean()
        
        # Analyze momentum
        closes = recent_data['close']
        momentum = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
        
        return {
            'higher_highs': higher_highs,
            'lower_lows': lower_lows,
            'avg_range': avg_range,
            'momentum': momentum,
            'is_trending': abs(momentum) > 5  # 5% threshold
        }

    def detect_market_regime(self,
                           df: pd.DataFrame,
                           volatility_window: int = 20,
                           trend_ema_periods: List[int] = [20, 50, 200],
                           momentum_threshold: float = 5.0) -> str:
        """
        Detect current market regime (trending, ranging, or volatile).
        
        Args:
            df: DataFrame with price data
            volatility_window: Window for volatility calculation
            trend_ema_periods: Periods for trend EMAs
            momentum_threshold: Threshold for momentum significance
            
        Returns:
            str: Market regime ('trending', 'ranging', 'volatile')
        """
        # Get trend analysis
        trend_info = self.identify_trend(df, trend_ema_periods)
        
        # Get price action analysis
        price_action = self.analyze_price_action(df, volatility_window)
        
        # Calculate volatility ratio
        recent_ranges = (df['high'] - df['low']).tail(volatility_window)
        current_volatility = recent_ranges.std()
        historical_volatility = recent_ranges.rolling(window=volatility_window*2).std().mean()
        volatility_ratio = current_volatility / historical_volatility if historical_volatility > 0 else 1.0
        
        # Determine regime
        if volatility_ratio > 1.5:  # High volatility
            regime = 'volatile'
        elif trend_info['trend'] in ['strong_bullish', 'strong_bearish']:
            regime = 'trending'
        else:
            regime = 'ranging'
        
        self.logger.log(f"Market Regime Analysis:")
        self.logger.log(f"Trend Strength: {trend_info['trend']}")
        self.logger.log(f"Volatility Ratio: {volatility_ratio:.2f}")
        self.logger.log(f"Momentum: {price_action['momentum']:.2f}%")
        self.logger.log(f"Detected Regime: {regime}")
        
        return regime

    def get_support_resistance(self,
                             df: pd.DataFrame,
                             window: int = 20,
                             threshold: float = 0.02) -> Tuple[float, float]:
        """
        Calculate dynamic support and resistance levels.
        
        Args:
            df: DataFrame with price data
            window: Lookback window
            threshold: Price cluster threshold
            
            Returns:
                Tuple of (support, resistance) levels
        """
        recent_data = df.tail(window)
        
        # Find price clusters
        price_points = pd.concat([recent_data['high'], recent_data['low']])
        clusters = pd.cut(price_points, bins=10)
        counts = clusters.value_counts()
        
        # Find significant levels
        significant_levels = []
        for level in counts.index:
            if counts[level] >= window * threshold:
                significant_levels.append(level.mid)
        
        if not significant_levels:
            return None, None
        
        # Get current price
        current_price = df['close'].iloc[-1]
        
        # Find nearest levels
        levels_array = np.array(significant_levels)
        support = levels_array[levels_array < current_price].max() if any(levels_array < current_price) else None
        resistance = levels_array[levels_array > current_price].min() if any(levels_array > current_price) else None
        
        return support, resistance

def add_market_regime(df: pd.DataFrame,
                     volatility_window: int = 20,
                     trend_ema_periods: List[int] = [20, 50, 200],
                     momentum_threshold: float = 5.0) -> pd.DataFrame:
    """
    Add market regime analysis to DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        volatility_window: Window for volatility calculation
        trend_ema_periods: Periods for trend EMAs
        momentum_threshold: Threshold for momentum significance
        
    Returns:
        DataFrame with added market regime columns
    """
    analyzer = MarketRegimeAnalyzer()
    
    # Initialize columns
    df['market_regime'] = None
    df['trend_strength'] = None
    df['support_level'] = None
    df['resistance_level'] = None
    
    # Calculate for each window
    for i in range(volatility_window, len(df)):
        window_df = df.iloc[:i+1]
        
        # Get market regime
        regime = analyzer.detect_market_regime(
            window_df,
            volatility_window=volatility_window,
            trend_ema_periods=trend_ema_periods,
            momentum_threshold=momentum_threshold
        )
        df.loc[window_df.index[-1], 'market_regime'] = regime
        
        # Get trend strength
        trend_info = analyzer.identify_trend(window_df, trend_ema_periods)
        df.loc[window_df.index[-1], 'trend_strength'] = trend_info['trend']
        
        # Get support/resistance levels
        support, resistance = analyzer.get_support_resistance(window_df)
        df.loc[window_df.index[-1], 'support_level'] = support
        df.loc[window_df.index[-1], 'resistance_level'] = resistance
    
    return df
