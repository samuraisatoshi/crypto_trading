"""
Candlestick analysis and feature engineering utilities.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def add_body_context(df: pd.DataFrame) -> pd.DataFrame:
    """Add candlestick body context features.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added body context features
    """
    try:
        # Validate input
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError("Missing required columns for body context calculation")
        
        # Body size and proportions
        df['body_size'] = abs(df['close'] - df['open'])
        df['body_to_wick_ratio'] = df['body_size'] / (df['high'] - df['low'])
        
        # Wick sizes
        df['upper_wick_size'] = abs(df['high'] - df[['close', 'open']].max(axis=1))
        df['lower_wick_size'] = abs(df[['close', 'open']].min(axis=1) - df['low'])
        
        # Body direction
        df['body_bullish'] = (df['close'] > df['open']).astype(int)
        df['body_bearish'] = (df['close'] < df['open']).astype(int)
        
        # Body significance
        df['body_significant'] = (df['body_size'] > 0.5 * df['body_size'].rolling(5).mean()).astype(int)
        
        # Body confirmation
        df['confirmed_by_body'] = (
            df['body_significant'] &
            df['body_bullish'] &
            (df['body_to_wick_ratio'] > 0.6)
        ).astype(int)
        
        return df
        
    except Exception as e:
        logger.error(f"Error adding body context: {str(e)}")
        raise

def add_price_action_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add price action analysis features.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added price action features
    """
    try:
        # Validate input
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError("Missing required columns for price action analysis")
        
        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['high_change'] = df['high'].pct_change()
        df['low_change'] = df['low'].pct_change()
        
        # Rolling statistics
        df['rolling_high'] = df['high'].rolling(window=20).max()
        df['rolling_low'] = df['low'].rolling(window=20).min()
        df['price_position'] = (df['close'] - df['rolling_low']) / (df['rolling_high'] - df['rolling_low'])
        
        # Volatility features
        df['range'] = df['high'] - df['low']
        df['range_ma'] = df['range'].rolling(window=20).mean()
        df['range_expansion'] = df['range'] / df['range_ma']
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        df['volume_price_trend'] = df['volume_ratio'] * df['price_change'].apply(np.sign)
        
        # Swing points
        df['swing_high'] = (
            (df['high'] > df['high'].shift(1)) &
            (df['high'] > df['high'].shift(-1))
        ).astype(int)
        
        df['swing_low'] = (
            (df['low'] < df['low'].shift(1)) &
            (df['low'] < df['low'].shift(-1))
        ).astype(int)
        
        # Trend features
        df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
        df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
        df['trend_strength'] = df['higher_high'].rolling(5).sum() - df['lower_low'].rolling(5).sum()
        
        return df
        
    except Exception as e:
        logger.error(f"Error adding price action features: {str(e)}")
        raise

def analyze_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Comprehensive candlestick analysis.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added candlestick analysis features
    """
    try:
        # Add body context features
        df = add_body_context(df)
        logger.debug("Added body context features")
        
        # Add price action features
        df = add_price_action_features(df)
        logger.debug("Added price action features")
        
        # Add pattern significance
        df['pattern_significance'] = (
            df['body_significant'] &
            (df['volume_ratio'] > 1.2) &
            ((df['swing_high'] == 1) | (df['swing_low'] == 1))
        ).astype(int)
        
        # Add trend context
        df['in_uptrend'] = (
            (df['trend_strength'] > 0) &
            (df['price_position'] > 0.5) &
            (df['volume_price_trend'] > 0)
        ).astype(int)
        
        df['in_downtrend'] = (
            (df['trend_strength'] < 0) &
            (df['price_position'] < 0.5) &
            (df['volume_price_trend'] < 0)
        ).astype(int)
        
        logger.info(f"Candlestick analysis complete. Shape: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error in candlestick analysis: {str(e)}")
        raise
