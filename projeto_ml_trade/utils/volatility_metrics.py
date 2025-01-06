"""
Volatility analysis and metrics calculation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from utils.indicators import calculate_atr, calculate_bollinger_bands
from utils.logging_helper import LoggingHelper

class VolatilityAnalyzer:
    """Analyzer for volatility metrics and regimes."""
    
    def __init__(self):
        """Initialize volatility analyzer."""
        self.logger = LoggingHelper()

    def calculate_volatility_ratio(self,
                                 df: pd.DataFrame,
                                 current_window: int = 20,
                                 historical_window: int = 60) -> float:
        """
        Calculate ratio of current to historical volatility.
        
        Args:
            df: DataFrame with price data
            current_window: Window for current volatility
            historical_window: Window for historical volatility
            
        Returns:
            float: Volatility ratio
        """
        # Calculate daily ranges
        ranges = df['high'] - df['low']
        
        # Calculate current volatility
        current_vol = ranges.tail(current_window).std()
        
        # Calculate historical volatility
        historical_vol = ranges.tail(historical_window).std()
        
        # Calculate ratio
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
        
        return vol_ratio

    def analyze_volatility(self,
                          df: pd.DataFrame,
                          lookback: int = 20,
                          atr_period: int = 14,
                          bb_period: int = 20,
                          bb_std: float = 2.0) -> Dict[str, any]:
        """
        Comprehensive volatility analysis.
        
        Args:
            df: DataFrame with price data
            lookback: Period for analysis
            atr_period: Period for ATR calculation
            bb_period: Period for Bollinger Bands
            bb_std: Standard deviations for Bollinger Bands
            
        Returns:
            Dictionary with volatility metrics
        """
        # Calculate ATR
        atr_data = calculate_atr(df['high'], df['low'], df['close'], atr_period)
        df['atr'] = atr_data['atr']
        
        # Calculate Bollinger Bands
        bb_data = calculate_bollinger_bands(df['close'], bb_period, bb_std)
        df['bb_upper'] = bb_data['bb_upper']
        df['bb_middle'] = bb_data['bb_middle']
        df['bb_lower'] = bb_data['bb_lower']
        
        # Get current values
        current = df.iloc[-1]
        
        # Calculate volatility ratio
        vol_ratio = self.calculate_volatility_ratio(df, lookback)
        
        # Calculate BB width
        bb_width = (current['bb_upper'] - current['bb_lower']) / current['bb_middle']
        historical_width = ((df['bb_upper'] - df['bb_lower']) / df['bb_middle']).tail(lookback).mean()
        squeeze_ratio = bb_width / historical_width
        
        # Calculate range ratio
        current_range = current['high'] - current['low']
        range_ratio = current_range / current['atr']
        
        # Calculate BB position
        bb_position = (current['close'] - current['bb_lower']) / (current['bb_upper'] - current['bb_lower'])
        
        return {
            'vol_ratio': vol_ratio,
            'range_ratio': range_ratio,
            'bb_position': bb_position,
            'squeeze_ratio': squeeze_ratio,
            'is_high_vol': vol_ratio > 1.5,
            'is_squeeze': squeeze_ratio < 0.8
        }

    def detect_breakout(self,
                       df: pd.DataFrame,
                       lookback: int = 5) -> Optional[str]:
        """
        Detect potential volatility breakout.
        
        Args:
            df: DataFrame with price data
            lookback: Period for breakout detection
            
        Returns:
            str: 'up', 'down', or None
        """
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check Bollinger Band breakout
        if current['close'] > current['bb_upper'] and previous['close'] <= previous['bb_upper']:
            return 'up'
        elif current['close'] < current['bb_lower'] and previous['close'] >= previous['bb_lower']:
            return 'down'
            
        return None

    def calculate_volatility_score(self,
                                 df: pd.DataFrame,
                                 vol_threshold: float = 1.5,
                                 range_threshold: float = 0.8) -> float:
        """
        Calculate composite volatility score.
        
        Args:
            df: DataFrame with price data
            vol_threshold: Threshold for high volatility
            range_threshold: Threshold for significant range
            
        Returns:
            float: Volatility score (0.0 to 1.0)
        """
        # Get volatility analysis
        vol_analysis = self.analyze_volatility(df)
        
        # Base score from volatility ratio
        base_score = min(vol_analysis['vol_ratio'] / vol_threshold, 1.0)
        
        # Adjust based on range significance
        if vol_analysis['range_ratio'] > range_threshold:
            base_score *= 1.2
        
        # Adjust based on squeeze
        if vol_analysis['squeeze_ratio'] < 0.8:
            base_score *= 1.1
            
        return min(base_score, 1.0)

    def get_volatility_regime(self, df: pd.DataFrame) -> str:
        """
        Determine current volatility regime.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            str: Volatility regime ('low', 'normal', 'high', 'extreme')
        """
        vol_score = self.calculate_volatility_score(df)
        
        if vol_score < 0.3:
            regime = 'low'
        elif vol_score < 0.7:
            regime = 'normal'
        elif vol_score < 0.9:
            regime = 'high'
        else:
            regime = 'extreme'
        
        self.logger.log(f"Volatility Analysis:")
        self.logger.log(f"Volatility Score: {vol_score:.2f}")
        self.logger.log(f"Volatility Regime: {regime}")
        
        return regime

    def adjust_position_size(self,
                           base_size: float,
                           df: pd.DataFrame,
                           vol_threshold: float = 1.5) -> float:
        """
        Adjust position size based on volatility conditions.
        
        Args:
            base_size: Base position size
            df: DataFrame with price data
            vol_threshold: Threshold for volatility adjustment
            
        Returns:
            float: Adjusted position size
        """
        # Get volatility analysis
        vol_analysis = self.analyze_volatility(df)
        
        # Adjust based on volatility conditions
        vol_multiplier = 1.0
        if vol_analysis['vol_ratio'] > vol_threshold:
            vol_multiplier = 0.8  # Reduce exposure in high volatility
        elif vol_analysis['squeeze_ratio'] < 0.8:
            vol_multiplier = 1.2  # Increase exposure in squeeze
            
        # Adjust based on range significance
        range_multiplier = 1.2 if vol_analysis['range_ratio'] > 0.8 else 0.8
        
        return min(base_size * vol_multiplier * range_multiplier, 1.0)

def add_volatility_metrics(df: pd.DataFrame,
                         lookback: int = 20,
                         atr_period: int = 14,
                         bb_period: int = 20,
                         bb_std: float = 2.0) -> pd.DataFrame:
    """
    Add volatility metrics to DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        lookback: Period for analysis
        atr_period: Period for ATR calculation
        bb_period: Period for Bollinger Bands
        bb_std: Standard deviations for Bollinger Bands
        
    Returns:
        DataFrame with added volatility metrics
    """
    analyzer = VolatilityAnalyzer()
    
    # Initialize columns
    df['volatility_regime'] = None
    df['volatility_score'] = None
    df['volatility_ratio'] = None
    df['squeeze_ratio'] = None
    df['breakout_direction'] = None
    
    # Calculate for each window
    for i in range(lookback, len(df)):
        window_df = df.iloc[:i+1]
        
        # Get volatility regime
        regime = analyzer.get_volatility_regime(window_df)
        df.loc[window_df.index[-1], 'volatility_regime'] = regime
        
        # Get volatility score
        score = analyzer.calculate_volatility_score(window_df)
        df.loc[window_df.index[-1], 'volatility_score'] = score
        
        # Get volatility analysis
        vol_analysis = analyzer.analyze_volatility(window_df)
        df.loc[window_df.index[-1], 'volatility_ratio'] = vol_analysis['vol_ratio']
        df.loc[window_df.index[-1], 'squeeze_ratio'] = vol_analysis['squeeze_ratio']
        
        # Get breakout direction
        breakout = analyzer.detect_breakout(window_df)
        df.loc[window_df.index[-1], 'breakout_direction'] = breakout
    
    return df
