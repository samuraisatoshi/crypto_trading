"""
Dataset-level indicator calculations.
"""
import pandas as pd
import numpy as np
from typing import Dict
from .moving_averages import calculate_sma, calculate_ema, calculate_macd, calculate_slope
from .oscillators import calculate_rsi, calculate_stochastic, calculate_adx
from .volatility import calculate_bollinger_bands, calculate_atr

def add_indicators_and_oscillators(df: pd.DataFrame) -> pd.DataFrame:
    """Add basic technical indicators and oscillators to DataFrame.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added indicators
    """
    # Moving Averages
    df['sma_20'] = calculate_sma(df['close'], 20)
    df['sma_50'] = calculate_sma(df['close'], 50)
    df['sma_200'] = calculate_sma(df['close'], 200)
    
    df['ema_12'] = calculate_ema(df['close'], 12)
    df['ema_26'] = calculate_ema(df['close'], 26)
    
    # RSI
    df['rsi'] = calculate_rsi(df['close'])
    
    # MACD
    macd_data = calculate_macd(df['close'])
    df['macd'] = macd_data['macd']
    df['macd_signal'] = macd_data['signal']
    df['macd_hist'] = macd_data['histogram']
    df['macd_divergence'] = macd_data['divergence']
    
    # Bollinger Bands
    bb_data = calculate_bollinger_bands(df['close'])
    df['bb_upper'] = bb_data['bb_upper']
    df['bb_middle'] = bb_data['bb_middle']
    df['bb_lower'] = bb_data['bb_lower']
    df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    df['bb_percent_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # ATR
    atr_data = calculate_atr(df['high'], df['low'], df['close'])
    df['atr'] = atr_data['atr']
    df['natr'] = atr_data['natr']
    
    # Stochastic
    stoch_data = calculate_stochastic(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch_data['k']
    df['stoch_d'] = stoch_data['d']
    
    # ADX
    adx_data = calculate_adx(df['high'], df['low'], df['close'])
    df['adx'] = adx_data['adx']
    df['plus_di'] = adx_data['pos_di']
    df['minus_di'] = adx_data['neg_di']
    
    return df

def add_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add advanced technical indicators to DataFrame."""
    # Price slopes
    df['slope_close'] = calculate_slope(df['close'])
    df['slope_volume'] = calculate_slope(df['volume'])
    
    # Moving average slopes
    df['slope_sma20'] = calculate_slope(df['sma_20'])
    df['slope_sma50'] = calculate_slope(df['sma_50'])
    
    # Indicator slopes
    df['slope_rsi'] = calculate_slope(df['rsi'])
    df['slope_macd'] = calculate_slope(df['macd'])
    
    # Indicator crosses
    df['ma_cross'] = np.where(
        (df['sma_20'] > df['sma_50']) & (df['sma_20'].shift(1) <= df['sma_50'].shift(1)),
        1,
        np.where(
            (df['sma_20'] < df['sma_50']) & (df['sma_20'].shift(1) >= df['sma_50'].shift(1)),
            -1,
            0
        )
    )
    
    df['macd_cross'] = np.where(
        (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)),
        1,
        np.where(
            (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)),
            -1,
            0
        )
    )
    
    return df
