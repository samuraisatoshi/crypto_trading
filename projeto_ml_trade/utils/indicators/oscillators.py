"""
Oscillator indicator calculations.
"""
import pandas as pd
import numpy as np
from typing import Dict
from .base import validate_data, IndicatorError
from .moving_averages import calculate_ema, calculate_sma

@validate_data
def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
        
    delta = series.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()
    
    for i in range(period, len(gains)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period-1) + gains.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period-1) + losses.iloc[i]) / period
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

@validate_data
def calculate_stochastic(high: pd.Series,
                        low: pd.Series,
                        close: pd.Series,
                        k_period: int = 14,
                        d_period: int = 3,
                        smooth_k: int = 3) -> Dict[str, pd.Series]:
    """Calculate Stochastic Oscillator."""
    if k_period <= 0 or d_period <= 0 or smooth_k <= 0:
        raise IndicatorError("Periods must be positive")
    
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    
    if smooth_k > 1:
        k = k.rolling(window=smooth_k).mean()
    
    d = k.rolling(window=d_period).mean()
    
    return {
        'k': k,
        'd': d
    }

@validate_data
def calculate_obv(close: pd.Series, volume: pd.Series) -> Dict[str, pd.Series]:
    """Calculate On Balance Volume with signal line."""
    direction = np.where(close > close.shift(1), 1, 
                        np.where(close < close.shift(1), -1, 0))
    obv = (direction * volume).cumsum()
    
    signal = calculate_ema(obv, 21)
    
    return {
        'obv': obv,
        'signal': signal,
        'histogram': obv - signal
    }

@validate_data
def calculate_adx(high: pd.Series,
                 low: pd.Series,
                 close: pd.Series,
                 period: int = 14) -> Dict[str, pd.Series]:
    """Calculate Average Directional Index."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Calculate smoothed values
    tr_smooth = pd.Series(0.0, index=tr.index)
    pos_dm_smooth = pd.Series(0.0, index=tr.index)
    neg_dm_smooth = pd.Series(0.0, index=tr.index)
    
    # Initialize first values
    tr_smooth.iloc[period-1] = tr.iloc[0:period].sum()
    pos_dm_smooth.iloc[period-1] = pd.Series(pos_dm).iloc[0:period].sum()
    neg_dm_smooth.iloc[period-1] = pd.Series(neg_dm).iloc[0:period].sum()
    
    # Calculate smoothed series
    for i in range(period, len(tr)):
        tr_smooth.iloc[i] = tr_smooth.iloc[i-1] - (tr_smooth.iloc[i-1]/period) + tr.iloc[i]
        pos_dm_smooth.iloc[i] = pos_dm_smooth.iloc[i-1] - (pos_dm_smooth.iloc[i-1]/period) + pos_dm[i]
        neg_dm_smooth.iloc[i] = neg_dm_smooth.iloc[i-1] - (neg_dm_smooth.iloc[i-1]/period) + neg_dm[i]
    
    # Calculate DI values
    pos_di = 100 * pos_dm_smooth / tr_smooth
    neg_di = 100 * neg_dm_smooth / tr_smooth
    
    # Calculate ADX
    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    adx = calculate_ema(dx, period)
    
    return {
        'adx': adx,
        'pos_di': pos_di,
        'neg_di': neg_di
    }
