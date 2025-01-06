"""
Volatility indicator calculations.
"""
import pandas as pd
from typing import Dict
from .base import validate_data, IndicatorError
from .moving_averages import calculate_sma

@validate_data
def calculate_bollinger_bands(series: pd.Series, 
                            period: int = 20, 
                            std_dev: float = 2.0) -> Dict[str, pd.Series]:
    """Calculate Bollinger Bands."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    if std_dev <= 0:
        raise IndicatorError("Standard deviation multiplier must be positive")
    
    middle_band = calculate_sma(series, period)
    std = series.rolling(window=period, min_periods=period).std()
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    bandwidth = (upper_band - lower_band) / middle_band
    percent_b = (series - lower_band) / (upper_band - lower_band)
    
    return {
        'bb_upper': upper_band,
        'bb_middle': middle_band,
        'bb_lower': lower_band,
        'bb_bandwidth': bandwidth,
        'bb_percent_b': percent_b
    }

@validate_data
def calculate_atr(high: pd.Series, 
                 low: pd.Series, 
                 close: pd.Series, 
                 period: int = 14) -> Dict[str, pd.Series]:
    """Calculate Average True Range."""
    if period <= 0:
        raise IndicatorError("Period must be positive")
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = pd.Series(index=tr.index, dtype=float)
    atr.iloc[period-1] = tr.iloc[0:period].mean()
    
    for i in range(period, len(tr)):
        atr.iloc[i] = (atr.iloc[i-1] * (period-1) + tr.iloc[i]) / period
    
    natr = (atr / close) * 100
    
    return {
        'atr': atr,
        'natr': natr
    }
