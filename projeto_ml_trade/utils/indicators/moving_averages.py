"""
Moving average indicator calculations.
"""
import pandas as pd
import numpy as np
from typing import Dict
from .base import validate_data, IndicatorError

@validate_data
def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    if period > len(series):
        raise IndicatorError("Period longer than series length")
    return series.rolling(window=period, min_periods=period).mean()

@validate_data
def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    if period > len(series):
        raise IndicatorError("Period longer than series length")
    return series.ewm(span=period, adjust=False, min_periods=period).mean()

@validate_data
def calculate_slope(series: pd.Series, period: int = 5) -> pd.Series:
    """Calculate linear regression slope."""
    if period <= 1:
        raise IndicatorError("Period must be greater than 1")
    
    slopes = pd.Series(index=series.index, dtype=float)
    x = np.arange(period)
    
    for i in range(period, len(series) + 1):
        y = series.iloc[i-period:i].values
        slope, _ = np.polyfit(x, y, 1)
        slopes.iloc[i-1] = slope
    
    return slopes

def calculate_macd_divergence(price: pd.Series, macd: pd.Series) -> pd.Series:
    """Calculate MACD divergence."""
    divergence = pd.Series(0, index=price.index)
    
    for i in range(20, len(price)):
        window = slice(i-20, i+1)
        
        price_high = price[window].max() == price.iloc[i]
        price_low = price[window].min() == price.iloc[i]
        
        macd_high = macd[window].max() == macd.iloc[i]
        macd_low = macd[window].min() == macd.iloc[i]
        
        if price_high and macd_low:
            divergence.iloc[i] = -1  # Bearish
        elif price_low and macd_high:
            divergence.iloc[i] = 1   # Bullish
            
    return divergence

@validate_data
def calculate_macd(series: pd.Series, 
                  fast_period: int = 12, 
                  slow_period: int = 26, 
                  signal_period: int = 9) -> Dict[str, pd.Series]:
    """Calculate Moving Average Convergence Divergence."""
    if fast_period >= slow_period:
        raise IndicatorError("Fast period must be less than slow period")
    
    fast_ema = calculate_ema(series, fast_period)
    slow_ema = calculate_ema(series, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram,
        'divergence': calculate_macd_divergence(series, macd_line)
    }
